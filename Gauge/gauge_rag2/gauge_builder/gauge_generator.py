"""
spec_generator.py
=================
Reads data/test_strategy.json and generates a Gauge .spec file
using the exploratory test format with real element IDs.

Step format produced:
    * Navigate to '/loan-calculator.html'
    * Enter '100000' into 'cloanamount'
    * Click 'x'
    * Verify: Page shows expected result

Usage:
    python gauge_builder/spec_generator.py
    python gauge_builder/spec_generator.py --input data/test_strategy.json --output specs/generated_test.spec
"""

import json, os, re, sys, argparse
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "https://www.calculator.net"
SEARCH_FIELD_ID = "calcSearchTerm"
SEARCH_BTN = "Search"

# ---------------------------------------------------------------------------
# Element ID knowledge base  (from exploratory spec + calculator.net DOM)
# ---------------------------------------------------------------------------

PAGE_ELEMENT_MAP = {
    "/loan-calculator.html": {
        "fields": {
            "loan amount": "cloanamount", "loan_amount": "cloanamount",
            "interest rate": "cinterestrate", "interest_rate": "cinterestrate",
            "loan term": "cloanterm", "loan_term": "cloanterm",
            "compounding frequency": "ccompound", "compounding_frequency": "ccompound",
        },
        "calculate_btn": "x", "clear_btn": "Clear",
    },
    "/mortgage-calculator.html": {
        "fields": {
            "loan amount": "chouseprice", "loan_amount": "chouseprice",
            "house price": "chouseprice", "house_price": "chouseprice",
            "down payment": "cdownpayment", "down_payment": "cdownpayment",
            "loan term": "cloanterm", "loan_term": "cloanterm",
            "interest rate": "cinterestrate", "interest_rate": "cinterestrate",
        },
        "calculate_btn": "See your local rates", "clear_btn": "Clear",
    },
    "/payment-calculator.html": {
        "fields": {
            "loan amount": "cloanamount", "loan_amount": "cloanamount",
            "interest rate": "cinterestrate", "interest_rate": "cinterestrate",
            "loan term": "cloanterm", "loan_term": "cloanterm",
        },
        "calculate_btn": "x", "clear_btn": "Clear",
    },
    "/auto-loan-calculator.html": {
        "fields": {
            "sale price": "csaleprice", "sale_price": "csaleprice",
            "loan term": "cloanterm", "loan_term": "cloanterm",
            "interest rate": "cinterestrate", "interest_rate": "cinterestrate",
            "incentive": "cincentive",
            "down payment": "cdownpayment", "down_payment": "cdownpayment",
            "trade in value": "ctradeinvalue", "trade_in_value": "ctradeinvalue",
            "trade in owned": "ctradeowned", "trade_in_owned": "ctradeowned",
            "down payment unit": "cdownpaymentunit", "down_payment_unit": "cdownpaymentunit",
            "state": "cstate",
            "sale tax": "csaletax", "sale_tax": "csaletax",
            "title and registration": "ctitle", "title_and_registration": "ctitle",
        },
        "calculate_btn": "x", "clear_btn": "Clear",
    },
    "/interest-calculator.html": {
        "fields": {
            "starting principal": "cstartingprinciple", "starting_principal": "cstartingprinciple",
            "loan amount": "cstartingprinciple", "loan_amount": "cstartingprinciple",
            "annual addition": "cannualaddition", "annual_addition": "cannualaddition",
            "interest rate": "cinterestrate", "interest_rate": "cinterestrate",
            "years": "cyears", "loan term": "cyears", "loan_term": "cyears",
            "compound frequency": "ccompound", "compound_frequency": "ccompound",
        },
        "calculate_btn": "x", "clear_btn": "Clear",
    },
    "/retirement-calculator.html": {
        "fields": {
            "current age": "cagenow", "current_age": "cagenow",
            "retirement age": "cretireage", "retirement_age": "cretireage",
            "life expectancy": "clifeexpectancy", "life_expectancy": "clifeexpectancy",
            "current income": "cincomenow", "current_income": "cincomenow",
            "income growth rate": "cincgrowth", "income_growth_rate": "cincgrowth",
            "desired retirement income": "cretireincome", "desired_retirement_income": "cretireincome",
            "income unit": "cincomeunit", "income_unit": "cincomeunit",
        },
        "calculate_btn": "x", "clear_btn": "Clear",
    },
    "/financial-calculator.html": {
        "fields": {
            # After clicking a calculator link, user lands on that calculator page
            # Use mortgage field IDs as defaults for E2E scenarios
            "loan amount": "chouseprice", "loan_amount": "chouseprice",
            "interest rate": "cinterestrate", "interest_rate": "cinterestrate",
            "loan term": "cloanterm", "loan_term": "cloanterm",
        },
        "calculate_btn": "See your local rates", "clear_btn": "Clear",
    },
    "/my-account/sign-in.php": {
        "fields": {"email": "email", "password": "password"},
        "calculate_btn": "submit", "clear_btn": "",
    },
    "/": {
        "fields": {"search term": SEARCH_FIELD_ID, "search_term": SEARCH_FIELD_ID},
        "calculate_btn": SEARCH_BTN, "clear_btn": "",
    },
}

# ---------------------------------------------------------------------------
# URL / config helpers
# ---------------------------------------------------------------------------

def url_to_path(url):
    url = url.strip().strip("'\"")
    if url.startswith("http"):
        return urlparse(url).path or "/"
    return url if url.startswith("/") else "/" + url

def get_page_config(url):
    path = url_to_path(url)
    if path in PAGE_ELEMENT_MAP:
        return PAGE_ELEMENT_MAP[path], path
    for key, cfg in PAGE_ELEMENT_MAP.items():
        if key in path or path in key:
            return cfg, path
    return {"fields": {}, "calculate_btn": "x", "clear_btn": "Clear"}, path

def get_field_id(concept, page_config):
    c = concept.lower().strip()
    fields = page_config.get("fields", {})
    if c in fields:
        return fields[c]
    for key, eid in fields.items():
        if key in c or c in key:
            return eid
    return "c" + re.sub(r"[^a-z0-9]", "", c)

# ---------------------------------------------------------------------------
# Step converters
# ---------------------------------------------------------------------------

def convert_step(raw, page_config, path):
    if isinstance(raw, dict):
        return _from_dict(raw, page_config, path)
    return _from_string(str(raw), page_config, path)

def _from_dict(step, page_config, path):
    action = step.get("action", "").lower()
    target = step.get("target", "")
    value  = step.get("value", "")
    desc   = step.get("description", "")
    if action == "navigate":
        p = url_to_path(value or target)
        return [f'Navigate to "{p}"']
    if action in ("input", "enter", "fill") and value and target:
        fid = get_field_id(target, page_config)
        return [f'Enter "{value}" into "{fid}"']
    if action == "click":
        return [f"Click '{target}'"]
    if action == "verify":
        if value not in ("page loaded", "form visible", ""):
            return [f"Verify: {desc or value}"]
        return ["Verify: Page loaded successfully"]
    return _from_string(desc or f"{action} {target} {value}".strip(), page_config, path)

def _from_string(raw, page_config, path):
    raw = raw.strip()

    # Navigate
    m = re.match(r'^navigate to ["\']?(https?://[^\s"\']+|/[^\s"\']*)["\']?$', raw, re.I)
    if m:
        return [f'Navigate to "{url_to_path(m.group(1))}"']

    # Enter search term -> two steps
    m = re.match(r'^enter search term ["\']?([^"\']*)["\']?$', raw, re.I)
    if m:
        term = m.group(1).strip() or "empty"
        return [f'Enter "{term}" into "{SEARCH_FIELD_ID}"', f'Click "{SEARCH_BTN}"']

    # Enter email
    m = re.match(r'^enter email ["\']?([^"\']+)["\']?$', raw, re.I)
    if m:
        return [f'Enter "{m.group(1)}" into "email"']

    # Enter password
    m = re.match(r'^enter password ["\']?([^"\']+)["\']?$', raw, re.I)
    if m:
        return [f'Enter "{m.group(1)}" into "password"']

    # Generic Enter <concept> <value>
    m = re.match(r'^enter (?:the )?(.+?)\s+["\']?([^"\']+)["\']?$', raw, re.I)
    if m:
        concept = m.group(1).strip().rstrip("\"'")
        value   = m.group(2).strip().strip("\"'")
        FIELD_KEYWORDS = r'amount|rate|term|price|age|income|tax|payment|email|password|search|frequency|unit|state|reg|incentive|trade|life|expectancy|growth|retirement|sale|principal|addition'
        if re.search(FIELD_KEYWORDS, concept, re.I):
            fid = get_field_id(concept, page_config)
            return [f'Enter "{value}" into "{fid}"']

    # Select
    m = re.match(r'^select (.+?)\s+["\']?([^"\']+)["\']?$', raw, re.I)
    if m:
        concept = m.group(1).strip()
        value   = m.group(2).strip().strip("\"'")
        fid = get_field_id(concept, page_config)
        return [f'Select "{value}" in "{fid}"']

    # Click buttons
    if re.match(r'^click the search button$', raw, re.I):
        return [f'Click "{SEARCH_BTN}"']
    if re.match(r'^click the (calculate|calc) button$', raw, re.I):
        return [f'Click "{page_config.get("calculate_btn", "x")}"']
    if re.match(r'^click the login button$', raw, re.I):
        return ["Click \"submit\""]
    if re.match(r'^click the clear button$', raw, re.I):
        return ["Click \"Clear\""]
    if re.match(r'^click the view amortization schedule button$', raw, re.I):
        return ["Click \"Show/Hide Amortization Schedule\""]
    if re.match(r'^click the view retirement planning options button$', raw, re.I):
        return ["Click \"Show Retirement Planning Options\""]
    m = re.match(r'^click the ["\']?(.+?)["\']? link$', raw, re.I)
    if m:
        return [f'Click "{m.group(1)}"']

    # Verify steps
    if re.match(r'^verify (the )?page (loads|loaded)', raw, re.I):
        return ["Verify: Page loaded successfully"]
    if re.match(r'^verify (the )?user is logged in$', raw, re.I):
        return ["Verify: User is logged in"]
    if re.match(r'^verify login was attempted$', raw, re.I):
        return ["Verify: Login was attempted"]
    if re.match(r'^verify search does not crash$', raw, re.I):
        return ["Verify: Search did not crash"]
    if re.match(r'^verify monthly payment is displayed$', raw, re.I):
        return ["Verify: Monthly payment is displayed"]
    if re.match(r'^verify amortization schedule is displayed$', raw, re.I):
        return ["Verify: Amortization schedule is displayed"]
    if re.match(r'^verify retirement result is displayed$', raw, re.I):
        return ["Verify: Retirement result is displayed"]
    if re.match(r'^form is visible$', raw, re.I):
        return ["Verify: Form is visible"]

    m = re.match(r'^verify the page contains ["\']?([^"\']+)["\']?$', raw, re.I)
    if m:
        return [f'Verify: Page contains "{m.group(1)}"']

    m = re.match(r'^verify (calculated result contains|page does not show valid result for) ["\']?([^"\']+)["\']?$', raw, re.I)
    if m:
        return [f'Verify: {m.group(1)} "{m.group(2)}"']

    if raw.lower().startswith("verify"):
        return [f'Verify: {raw[7:].strip()}']

    return []

# ---------------------------------------------------------------------------
# Spec builder
# ---------------------------------------------------------------------------

SPEC_HEADER = "# calculator.net Automated Test Suite\n"

def build_spec(strategy):
    lines = [SPEC_HEADER, ""]
    for page in strategy:
        url = page.get("url", "")
        module = page.get("module_name", "")
        page_config, path = get_page_config(url)

        for sc in page.get("test_scenarios", []):
            steps_raw = sc.get("steps", [])
            if not steps_raw:
                continue

            gauge_steps = [f'Navigate to "{path}"']
            for raw in steps_raw:
                for s in convert_step(raw, page_config, path):
                    # Skip duplicate consecutive steps
                    if gauge_steps and gauge_steps[-1] == s:
                        continue
                    gauge_steps.append(s)

            if len(gauge_steps) < 2:
                continue

            sc_id  = sc.get("scenario_id", "TC_000")
            title  = sc.get("title", "Untitled")
            tags   = [t.replace("-", "_") for t in sc.get("tags", [])]
            prefix = f"{module}_{sc_id}" if module else sc_id

            lines.append(f"  ## {prefix}: {title}")
            if tags:
                lines.append(f"  tags: {', '.join(tags)}")
            lines.append("")
            for s in gauge_steps:
                lines.append(f"  * {s}")
            lines.append("")

    return "\n".join(lines)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate Gauge .spec with element IDs from test_strategy.json")
    parser.add_argument("--input",  "-i", default="data/test_strategy.json", metavar="FILE")
    parser.add_argument("--output", "-o", default="specs/generated_test.spec", metavar="FILE")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[ERROR] Not found: {input_path}"); sys.exit(1)

    with open(input_path, encoding="utf-8") as f:
        strategy = json.load(f)

    print(f"[INFO] Loaded {len(strategy)} page entries from {input_path}")
    spec = build_spec(strategy)

    scenarios = spec.count("\n  ## ")
    steps     = spec.count("\n  * ")
    print(f"[INFO] Generated {scenarios} scenarios, {steps} steps")

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(spec, encoding="utf-8")
    print(f"[OK]  Spec written to: {out.resolve()}")

    print("\n--- Preview (first 70 lines) ---")
    for line in spec.splitlines()[:70]:
        print(line)

if __name__ == "__main__":
    main()