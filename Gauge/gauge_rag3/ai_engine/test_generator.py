"""
ai_engine/test_generator.py
============================
Reads crawled metadata JSON, calls Groq AI with RAG context,
and writes a testcases.json file.

HOW TO RUN (from the project root folder):
    python ai_engine/test_generator.py

ALL SETTINGS ARE HARDCODED BELOW — edit and run.
No config file, no CLI arguments, no relative imports.
"""

import json
import logging
import re
import os
import sys
from datetime import datetime
from typing import Optional

# Add project root to path so sibling modules can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_engine.groq_client import GroqClient
from rag.retriever import retrieve_for_page

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# =============================================================================
#  SETTINGS — edit these values directly
# =============================================================================

METADATA_FILE    = "data/metadata/metadata.json"      # output from web_crawler.py
OUTPUT_FILE      = "data/testcases/testcases.json"     # where to save test cases

USE_RAG          = True    # False = skip RAG, pure Groq only

# Process only specific page indices? e.g. [0, 1, 2]  or  None = all pages
PAGES_TO_PROCESS = None

# =============================================================================

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

# ── Prompt ────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a senior QA automation engineer with 10+ years of web testing experience.
You will be given real element data crawled from a live web page.

CRITICAL RULES — SELECTORS:
1. ONLY use selector_value strings that appear EXACTLY in the ELEMENTS data provided.
2. NEVER invent or guess element IDs, names, or CSS classes (e.g. do not use id=amount, id=salary, id=loanamount unless those exact strings appear in the ELEMENTS data).
3. For each form field, use the "selector" value from its entry in the ELEMENTS data.
4. For navigation links, use the "selector" value from its entry in the ELEMENTS data.
5. For buttons, use the "selector" value from its entry in the ELEMENTS data.
6. If a step needs to navigate to a URL, use the EXACT page URL provided.
7. Each test MUST start with a "navigate" action to the page URL — never assume the browser is already on the right page.

CRITICAL RULES — TEST STRUCTURE:
- First step of EVERY test case must be: action=navigate, selector_type=css, selector_value=<the page URL>
- Only test elements that exist in the ELEMENTS data
- Use realistic input values (numbers for number fields, text for text fields)
- Cover: happy path, empty required fields, invalid format

OUTPUT FORMAT — return ONLY valid JSON, no markdown, no text outside the JSON:
{
  "test_suite": "Suite name",
  "url": "page url",
  "page_type": "page type",
  "test_cases": [
    {
      "id": "TC_001",
      "name": "Short descriptive name",
      "category": "functional|navigation|form|ui|accessibility|e2e",
      "priority": "high|medium|low",
      "description": "What this test verifies",
      "preconditions": ["Navigate to page URL"],
      "steps": [
        {
          "step_number": 1,
          "action": "navigate",
          "target": {
            "element_type": "page",
            "selector_type": "css",
            "selector_value": "REPLACE_WITH_EXACT_PAGE_URL",
            "description": "Navigate to the page"
          },
          "input_data": null,
          "expected_result": "Page loads successfully"
        },
        {
          "step_number": 2,
          "action": "navigate|click|type|verify|select|hover|wait|assert_text|assert_visible|assert_url|clear|scroll",
          "target": {
            "element_type": "button|input|link|select|form|page",
            "selector_type": "id|css|xpath|name",
            "selector_value": "USE_EXACT_SELECTOR_FROM_ELEMENTS_DATA",
            "description": "human label"
          },
          "input_data": "text to enter, or null",
          "expected_result": "what should happen"
        }
      ],
      "expected_outcome": "Final state after all steps",
      "tags": ["smoke"]
    }
  ]
}"""


def _build_prompt(page_data, rag_context=""):
    e = page_data.get("elements", {})
    page_url = page_data.get("url", "unknown")

    rag_block = (
        "\nRELEVANT CONTEXT FROM KNOWLEDGE BASE:\n" + rag_context + "\n--- END CONTEXT ---\n"
    ) if rag_context.strip() else ""

    # ── Selector Reference Block ───────────────────────────────────────────────
    # Build a clean, unambiguous list the AI must use verbatim.
    # Key insight from metadata analysis:
    #   - All nav links have selector={"type":"xpath","value":"//a"} which is generic
    #     → Use link_text strategy with actual text value instead
    #   - Form fields have proper id/name selectors → use those directly
    #   - Buttons have name=x (Calculate) → use that

    selector_ref = []
    has_form_fields = False

    # Form fields — emit as  INPUT  type=id  value=cloanamount  name=cloanamount
    seen_fields = set()
    for form in e.get("forms", [])[:5]:
        for f in form.get("fields", [])[:15]:
            sel = f.get("selector", {})
            sel_type = sel.get("type", "") if isinstance(sel, dict) else ""
            sel_val  = sel.get("value", "") if isinstance(sel, dict) else str(sel)
            name     = f.get("name", "")
            ftype    = f.get("element_type", "input")
            label    = f.get("label", "") or f.get("placeholder", "") or name
            key      = f"{sel_type}={sel_val}"
            if key not in seen_fields and sel_val and sel_val not in ("//input", "//textarea"):
                seen_fields.add(key)
                selector_ref.append(
                    f"  INPUT   selector_type={sel_type}  selector_value={sel_val}"
                    f"  name={name}  type={ftype}  label={label}"
                )
                has_form_fields = True
        for btn in form.get("submit_buttons", []):
            sel = btn.get("selector", {})
            sel_type = sel.get("type", "") if isinstance(sel, dict) else ""
            sel_val  = sel.get("value", "") if isinstance(sel, dict) else str(sel)
            txt = btn.get("value", btn.get("text", ""))
            if sel_val and sel_val not in ("//input",):
                selector_ref.append(
                    f"  BUTTON  selector_type={sel_type}  selector_value={sel_val}  text={txt}"
                )

    # Interactive buttons (deduplicated)
    seen_btns = set()
    for el in e.get("interactive", [])[:10]:
        sel = el.get("selector", {})
        sel_type = sel.get("type", "") if isinstance(sel, dict) else ""
        sel_val  = sel.get("value", "") if isinstance(sel, dict) else str(sel)
        txt = el.get("text", "")[:40]
        key = f"{sel_type}={sel_val}"
        if key not in seen_btns and sel_val and sel_val not in ("//input",):
            seen_btns.add(key)
            selector_ref.append(
                f"  BUTTON  selector_type={sel_type}  selector_value={sel_val}  text={txt}"
            )

    # Navigation links — ALL crawled links have selector=//a (generic xpath).
    # The ONLY reliable way to click them is By.LINK_TEXT with exact text.
    # Emit link_text entries so AI knows to use selector_type=link_text.
    seen_txt = set()
    for link in e.get("navigation", []):
        txt  = link.get("text", "").strip()
        href = link.get("href", "")[:80]
        if txt and txt not in seen_txt and not link.get("is_external"):
            seen_txt.add(txt)
            selector_ref.append(
                f"  LINK    selector_type=link_text  selector_value={txt}  href={href}"
            )
        if len(seen_txt) >= 10:
            break

    # Headings — use xpath //h1, css h2.h2red, etc. from metadata
    for h in e.get("content", [])[:5]:
        sel = h.get("selector", {})
        sel_type = sel.get("type", "") if isinstance(sel, dict) else ""
        sel_val  = sel.get("value", "") if isinstance(sel, dict) else str(sel)
        level    = h.get("level", "")
        text     = h.get("text", "")[:50]
        selector_ref.append(
            f"  HEADING selector_type={sel_type}  selector_value={sel_val}"
            f"  level={level}  text={text}"
        )

    selector_block = "\n".join(selector_ref) if selector_ref else "  (no selectors found)"

    # Warn AI explicitly if no form fields were found
    no_form_warning = ""
    if not has_form_fields:
        no_form_warning = (
            "\nWARNING: No form fields were found for this page in the crawl data. "
            "DO NOT generate form interaction steps (type/clear/enter). "
            "Only generate: navigate, assert_visible (headings/page elements), assert_url, "
            "and click steps using the LINK selectors above.\n"
        )

    user_prompt = (
        f"Generate comprehensive test cases for this page.\n\n"
        f"PAGE URL: {page_url}\n"
        f"Title: {page_data.get('title', 'unknown')}\n"
        f"Type: {page_data.get('page_type', 'general')}\n"
        f"{rag_block}"
        f"{no_form_warning}\n"
        f"=== VERIFIED SELECTORS — USE ONLY THESE, DO NOT INVENT ANY ===\n"
        f"{selector_block}\n"
        f"=== END SELECTORS ===\n\n"
        f"RULES:\n"
        f"1. First step of EVERY test: action=navigate, selector_type=css, selector_value={page_url}\n"
        f"2. For INPUT steps: use selector_type and selector_value exactly as listed above\n"
        f"3. For LINK clicks: use selector_type=link_text, selector_value=<exact text from LINK entries>\n"
        f"4. NEVER invent IDs like id=amount, id=salary, id=title, id=home-link\n"
        f"5. NEVER use selector_type=link_text with text not listed above\n"
        f"6. For headings/visibility: use selector_type and selector_value from HEADING entries\n"
        f"Return ONLY the JSON object."
    )

    words = user_prompt.split()
    if len(words) > 3000:
        user_prompt = " ".join(words[:3000]) + "\n\n[TRUNCATED] Generate test cases from above only."

    return SYSTEM_PROMPT, user_prompt


# ── Parsing ───────────────────────────────────────────────────────────────────

def _parse(response, url, page_type):
    try:
        data = json.loads(response)
    except:
        data = _salvage(response)
    if not data:
        return []
    raw = data.get("test_cases", data) if isinstance(data, dict) else data
    if isinstance(raw, dict) and "steps" in raw:
        raw = [raw]
    if not isinstance(raw, list):
        return []
    return [c for c in (_validate(tc, url, page_type) for tc in raw) if c]


def _ensure_navigate_first(tc, url):
    """Guarantee every test case starts with a navigate step to the page URL."""
    steps = tc.get("steps", [])
    if not steps:
        return tc
    first = steps[0]
    if first.get("action") != "navigate":
        nav_step = {
            "step_number": 1,
            "action": "navigate",
            "target": {
                "element_type": "page",
                "selector_type": "css",
                "selector_value": url,
                "description": f"Navigate to {url}"
            },
            "input_data": None,
            "expected_result": "Page loads successfully"
        }
        # Renumber existing steps
        for i, s in enumerate(steps):
            s["step_number"] = i + 2
        tc["steps"] = [nav_step] + steps
        logger.debug(f"  Injected navigate step for: {tc.get('name')}")
    else:
        # Ensure the navigate URL is the real page URL not a placeholder
        sv = first.get("target", {}).get("selector_value", "")
        if not sv.startswith("http") or "REPLACE" in sv or "EXACT" in sv:
            first["target"]["selector_value"] = url
    return tc


def _salvage(text) -> Optional[dict]:
    for pat in [r'\{[\s\S]*"test_cases"[\s\S]*\}', r'\[[\s\S]*\]']:
        m = re.search(pat, text)
        if m:
            try: return json.loads(m.group())
            except: continue
    return None


def _validate(tc, url, page_type):
    if not isinstance(tc, dict) or not tc.get("steps"):
        return None
    tc.setdefault("id",              "TC_000")
    tc.setdefault("name",            "Unnamed Test")
    tc.setdefault("category",        "functional")
    tc.setdefault("priority",        "medium")
    tc.setdefault("description",     "Auto-generated")
    tc.setdefault("preconditions",   [f"Navigate to {url}"])
    tc.setdefault("expected_outcome","Test passes")
    tc.setdefault("tags",            [page_type, "auto-generated"])
    for i, step in enumerate(tc["steps"]):
        step.setdefault("step_number",    i + 1)
        step.setdefault("action",         "verify")
        step.setdefault("input_data",     None)
        step.setdefault("expected_result","Step completes")
        step.setdefault("target", {"element_type": "page", "selector_type": "css",
                                   "selector_value": "body", "description": "Page"})
    # Ensure first step navigates to the correct page URL
    tc = _ensure_navigate_first(tc, url)
    return tc


# ── Post-processor ────────────────────────────────────────────────────────────
# Runs on the FULL list of generated test cases to catch residual hallucinations.

# All real link texts from the crawled metadata (exact, case-sensitive)
REAL_LINK_TEXTS = {
    "sign in", "Mortgage Calculator", "Loan Calculator", "Auto Loan Calculator",
    "Interest Calculator", "Payment Calculator", "Retirement Calculator",
    "Amortization Calculator", "Investment Calculator", "Inflation Calculator",
    "Finance Calculator", "Income Tax Calculator", "Compound Interest Calculator",
    "Salary Calculator", "Interest Rate Calculator", "Sales Tax Calculator",
    "BMI Calculator", "Calorie Calculator", "Body Fat Calculator", "BMR Calculator",
    "Ideal Weight Calculator", "Pace Calculator", "Pregnancy Calculator",
    "Pregnancy Conception Calculator", "Due Date Calculator", "Scientific Calculator",
    "Fraction Calculator", "Percentage Calculator", "Random Number Generator",
    "Triangle Calculator", "Standard Deviation Calculator", "Age Calculator",
    "Date Calculator", "Time Calculator", "Hours Calculator", "GPA Calculator",
    "Grade Calculator", "Concrete Calculator", "Subnet Calculator",
    "Password Generator", "Conversion Calculator",
    "about us", "sitemap", "terms of use", "privacy policy",
    "financial", "fitness & health", "math", "other", "others",
    "loan calculator", "interest rate calculator", "sales tax calculator",
    "salary calculator", "credit card calculator", "credit card payoff calculator",
    "financial", "Fitness and Health", "Financial", "Math", "Other",
    "Mortgage", "Loan", "Auto Loan", "Interest", "Payment", "Retirement",
    "Amortization", "Investment", "Currency", "Inflation", "Finance",
    "Mortgage Payoff", "Income Tax", "Salary", "401K", "Interest Rate", "Sales Tax",
    "mortgages", "auto loans", "student loans", "personal loans",
    "View Amortization Table", "FHA Loan Calculator", "VA Mortgage Calculator",
    "Business Loan Calculator", "APR Calculator", "Credit Card Calculator",
    "Debt Consolidation Calculator",
    "VAT Calculator",
    "Take Home Pay Calculator",
    "Percent Error Calculator", "Exponent Calculator", "Binary Calculator",
}

# Pages where the crawler captured NO real form fields — any step using a form
# field selector on these pages is a hallucination fallback.
PAGES_WITH_NO_FORM_FIELDS = {
    "https://www.calculator.net/loan-calculator.html",
    "https://www.calculator.net/loan-calculator.html#fixedend",
    "https://www.calculator.net/loan-calculator.html#monthlyfixed",
    "https://www.calculator.net/loan-calculator.html#intheend",
    "https://www.calculator.net/math-calculator.html",
    "https://www.calculator.net/",
    "https://www.calculator.net/other-calculator.html",
}

# The search box is the ONLY input on many pages — its selector must not be
# used as a calculator form field.
SEARCH_BOX_SELECTOR = "calcSearchTerm"


def _postprocess_all(test_cases: list) -> list:
    """Clean hallucinations from the full generated test case list."""
    cleaned, dropped_total, fixed_total = [], 0, 0

    for tc in test_cases:
        url = ""
        # Determine which page this TC belongs to from its navigate step
        for step in tc.get("steps", []):
            if step.get("action") == "navigate":
                url = step.get("target", {}).get("selector_value", "")
                break

        new_steps = []
        drop_tc = False

        for step in tc.get("steps", []):
            action = step.get("action", "")
            t = step.get("target", {})
            sel_type  = t.get("selector_type", "")
            sel_value = t.get("selector_value", "")

            # ── Fix 1: Remove form-interaction steps on pages with no form fields
            # These are steps that use calcSearchTerm as a fake "loan amount" field
            if action in ("type", "clear") and sel_value == SEARCH_BOX_SELECTOR:
                if url in PAGES_WITH_NO_FORM_FIELDS:
                    # Drop this step — it's the search box being misused
                    fixed_total += 1
                    logger.debug(f"  POST: Removed fake form step (calcSearchTerm) in {tc['id']}")
                    continue  # skip this step

            # ── Fix 2: Validate link_text values against real navigation texts
            if sel_type == "link_text" and action == "click":
                if sel_value not in REAL_LINK_TEXTS:
                    # Check case-insensitive match first
                    ci_match = next(
                        (r for r in REAL_LINK_TEXTS if r.lower() == sel_value.lower()), None
                    )
                    if ci_match:
                        # Fix case mismatch (e.g. "Sign in" → "sign in")
                        t["selector_value"] = ci_match
                        fixed_total += 1
                        logger.debug(f"  POST: Fixed link_text case '{sel_value}'→'{ci_match}' in {tc['id']}")
                    else:
                        # Hallucinated link text — drop this step
                        fixed_total += 1
                        logger.debug(f"  POST: Removed hallucinated link_text='{sel_value}' in {tc['id']}")
                        continue  # skip this step

            new_steps.append(step)

        # If after cleaning a TC has only 1 step (just navigate) and was originally
        # a form test, it's now meaningless — drop it entirely
        navigate_only = len(new_steps) == 1 and new_steps[0].get("action") == "navigate"
        original_had_form = any(
            s.get("action") in ("type", "clear") for s in tc.get("steps", [])
        )
        if navigate_only and original_had_form:
            dropped_total += 1
            logger.info(f"  POST: Dropped TC {tc['id']} '{tc.get('name')}' — all form steps removed (page has no form fields)")
            continue

        tc["steps"] = new_steps
        cleaned.append(tc)

    logger.info(f"\nPost-processor: {fixed_total} steps fixed/removed, {dropped_total} TCs dropped")
    return cleaned


# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    logger.info(f"\n{'='*55}")
    logger.info(f"TEST GENERATOR")
    logger.info(f"  metadata : {METADATA_FILE}")
    logger.info(f"  output   : {OUTPUT_FILE}")
    logger.info(f"  use_rag  : {USE_RAG}")
    logger.info(f"{'='*55}")

    if not os.path.isfile(METADATA_FILE):
        raise FileNotFoundError(
            f"File not found: {METADATA_FILE}\n"
            f"Run crawler/web_crawler.py first."
        )

    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    pages    = metadata.get("pages", [])
    base_url = metadata.get("crawl_metadata", {}).get("base_url", "unknown")

    if PAGES_TO_PROCESS is not None:
        pages = [pages[i] for i in PAGES_TO_PROCESS if i < len(pages)]

    logger.info(f"  base_url : {base_url}")
    logger.info(f"  pages    : {len(pages)}\n")

    client  = GroqClient()
    all_tcs = []
    failed  = []
    tc_num  = 1

    for i, page in enumerate(pages):
        url = page.get("url", "unknown")
        logger.info(f"\n[{i+1}/{len(pages)}] {url}")
        try:
            rag_ctx = retrieve_for_page(page) if USE_RAG else ""
            sys_p, usr_p = _build_prompt(page, rag_ctx)
            response = client.complete(sys_p, usr_p, expect_json=True)

            if not response:
                logger.error("No response from Groq")
                failed.append(url)
                continue

            tcs = _parse(response, url, page.get("page_type", "general"))
            for tc in tcs:
                tc["id"] = f"TC_{tc_num:03d}"
                tc_num += 1
            all_tcs.extend(tcs)
            logger.info(f"  {len(tcs)} test cases generated")
        except Exception as ex:
            logger.error(f"  Error: {ex}")
            failed.append(url)

    if failed:
        logger.warning(f"\nFailed pages: {failed}")

    # ── Post-process: remove hallucinations, fix link text case ───────────────
    all_tcs = _postprocess_all(all_tcs)
    # Re-number IDs after dropping tests
    for i, tc in enumerate(all_tcs, 1):
        tc["id"] = f"TC_{i:03d}"

    u = client.usage()
    logger.info(f"\nGroq: {u['calls']} calls, {u['tokens']} tokens")

    cats: dict = {}
    pris: dict = {}
    for tc in all_tcs:
        c = tc.get("category", "functional"); p = tc.get("priority", "medium")
        cats[c] = cats.get(c, 0) + 1;        pris[p] = pris.get(p, 0) + 1

    output = {
        "generation_metadata": {
            "base_url":         base_url,
            "generated_at":     datetime.now().isoformat(),
            "total_test_cases": len(all_tcs),
            "rag_enabled":      USE_RAG,
        },
        "statistics": {"by_category": cats, "by_priority": pris, "total": len(all_tcs)},
        "test_cases": all_tcs,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    logger.info(f"\nDone — {len(all_tcs)} test cases saved to {OUTPUT_FILE}")
    logger.info(f"\nNext steps:")
    logger.info(f"  python gauge_generator/spec_generator.py")
    logger.info(f"  python gauge_generator/step_impl_generator.py")


if __name__ == "__main__":
    run()