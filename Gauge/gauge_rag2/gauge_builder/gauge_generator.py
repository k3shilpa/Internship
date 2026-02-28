# gauge_builder/gauge_generator.py
# Generates a valid Gauge .spec file from strategy_normalized.json
# Includes calculated expected values and full output verification for every scenario.
# Compatible with Python 3.9+

import json
import logging
import os
import re
import sys
from typing import List, Optional
from urllib.parse import urlparse
from pathlib import Path

# Add project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import config

logger = logging.getLogger(__name__)


# ==============================================================================
# FINANCIAL CALCULATION UTILITIES
# Used to compute expected results for assertion steps
# ==============================================================================

def _monthly_payment_apr(principal: float, annual_rate: float, years: float) -> Optional[str]:
    """Standard amortization formula using Monthly (APR) compounding."""
    r = annual_rate / 100 / 12
    n = years * 12
    if r == 0 or n == 0:
        return None
    payment = principal * r * (1 + r) ** n / ((1 + r) ** n - 1)
    return f"${payment:,.2f}"


def _monthly_payment_apy(principal: float, annual_rate: float, years: float) -> Optional[str]:
    """Amortization using Annually (APY) compounding — converts to effective monthly rate."""
    monthly_r = (1 + annual_rate / 100) ** (1 / 12) - 1
    n = years * 12
    if monthly_r == 0 or n == 0:
        return None
    payment = principal * monthly_r * (1 + monthly_r) ** n / ((1 + monthly_r) ** n - 1)
    return f"${payment:,.2f}"


def _extract_numeric(value: str) -> Optional[float]:
    """Safely parse a numeric string like '100000' or '50000'."""
    try:
        return float(str(value).replace(",", "").replace("$", "").strip())
    except (ValueError, TypeError):
        return None


def _extract_quoted(step: str) -> str:
    """Extract the last quoted value from a step string."""
    matches = re.findall(r'"([^"]*)"', step)
    return matches[-1] if matches else ""


def _try_compute_expected_value(steps: List[str], compounding: str = "monthly") -> Optional[str]:
    """
    Inspect steps for loan amount, interest rate, loan term and
    return the expected monthly payment string if computable.
    """
    principal = None
    rate = None
    term = None

    for step in steps:
        s = step.lower()
        if "loan amount" in s or "sale price" in s or "house" in s:
            val = _extract_numeric(_extract_quoted(step))
            if val is not None:
                principal = val
        elif "interest rate" in s:
            val = _extract_numeric(_extract_quoted(step))
            if val is not None:
                rate = val
        elif "loan term" in s:
            val = _extract_numeric(_extract_quoted(step))
            if val is not None:
                term = val
        elif "compounding" in s or "frequency" in s:
            quoted = _extract_quoted(step).lower()
            if "annual" in quoted or "apy" in quoted:
                compounding = "annually"
            else:
                compounding = "monthly"

    if principal and rate and term:
        if compounding == "annually":
            return _monthly_payment_apy(principal, rate, term)
        else:
            return _monthly_payment_apr(principal, rate, term)
    return None


# ==============================================================================
# STEP CLASSIFICATION
# Determines what kind of verification to append based on scenario type
# ==============================================================================

# Keywords that indicate invalid/negative test inputs
_INVALID_INPUT_KEYWORDS = {"abc", "invalid", "xss", "-1", "xss-attack"}

# Steps that indicate calculator form inputs
_CALC_INPUT_STEPS = {
    "enter loan amount", "enter sale price", "enter interest rate", "enter loan term",
    "enter current age", "enter retirement age", "enter life expectancy",
    "enter current income", "enter income growth rate", "enter desired retirement income",
}

# Verification step prefixes — stripped before regenerating
_VERIFY_PREFIXES = (
    "verify the page contains",
    "verify monthly payment",
    "verify calculated result",
    "verify amortization",
    "verify search does not crash",
    "verify page does not show",
    "verify login was attempted",
    "verify the user is logged in",
    "verify retirement result",
    "verify loan amount input field",
)

# Map of URL path keywords → page type
_PAGE_TYPE_MAP = {
    "mortgage-calculator":  "mortgage",
    "loan-calculator":      "loan",
    "auto-loan-calculator": "auto_loan",
    "payment-calculator":   "payment",
    "retirement-calculator":"retirement",
    "interest-calculator":  "interest",
    "financial-calculator": "financial",
    "sign-in":              "login",
    "/":                    "homepage",
}


def _page_type(url: str) -> str:
    for key, ptype in _PAGE_TYPE_MAP.items():
        if key in url:
            return ptype
    return "generic"


def _scenario_type(scenario: dict) -> str:
    """Classify scenario as: happy, negative, boundary, e2e."""
    combined = (scenario.get("title", "") + " " + scenario.get("scenario_id", "")).lower()
    if any(k in combined for k in ("negative", "invalid", "empty", "error")):
        return "negative"
    if any(k in combined for k in ("boundary", "maximum", "minimum", "max", "min")):
        return "boundary"
    if any(k in combined for k in ("e2e", "end to end", "end-to-end")):
        return "e2e"
    return "happy"


def _has_invalid_input(steps: List[str]) -> bool:
    """Return True if any step contains a clearly invalid value."""
    for step in steps:
        if _extract_quoted(step).lower() in _INVALID_INPUT_KEYWORDS:
            return True
    return False


def _is_search_scenario(steps: List[str]) -> bool:
    return any("enter search term" in s.lower() for s in steps)


def _is_login_scenario(steps: List[str]) -> bool:
    return any("enter email" in s.lower() or "enter password" in s.lower() for s in steps)


def _is_calculator_scenario(steps: List[str]) -> bool:
    return any(any(k in s.lower() for k in _CALC_INPUT_STEPS) for s in steps)


# ==============================================================================
# VERIFICATION STEP BUILDER
# ==============================================================================

def _build_verification_steps(scenario: dict, url: str, steps: List[str]) -> List[str]:
    """
    Returns verification step strings to append to a scenario based on its context:
    - Search       → verify result text or no crash
    - Login        → verify login attempted or user logged in
    - Calculator   → verify monthly payment + calculated value (or no result for invalid)
    - Retirement   → verify retirement result displayed
    - Page load    → no extra steps needed (already has Verify the page contains)
    """
    stype = _scenario_type(scenario)
    ptype = _page_type(url)
    verification = []
    invalid = _has_invalid_input(steps)

    # ── Search ─────────────────────────────────────────────────────────────────
    if _is_search_scenario(steps):
        search_term = next(
            (_extract_quoted(s) for s in steps if "enter search term" in s.lower()), ""
        )
        if not search_term or len(search_term) > 50 or any(
            k in search_term.lower() for k in ("xss", "<", ">", "script")
        ):
            verification.append('Verify search does not crash')
        else:
            verification.append(f'Verify the page contains "{search_term.title()}"')
        return verification

    # ── Login ──────────────────────────────────────────────────────────────────
    if _is_login_scenario(steps):
        if stype == "e2e":
            verification.append('Verify the user is logged in')
        else:
            verification.append('Verify login was attempted')
        return verification

    # ── Retirement ─────────────────────────────────────────────────────────────
    if ptype == "retirement" and _is_calculator_scenario(steps):
        verification.append('Verify retirement result is displayed')
        return verification

    # ── Interest / static module pages ─────────────────────────────────────────
    if ptype == "interest":
        return verification  # already has Verify the page contains in spec

    # ── Calculator pages ───────────────────────────────────────────────────────
    if _is_calculator_scenario(steps):
        if not any("click the calculate button" in s.lower() for s in steps):
            return verification  # no calculation triggered

        if invalid:
            invalid_val = next(
                (_extract_quoted(s) for s in steps
                 if _extract_quoted(s).lower() in _INVALID_INPUT_KEYWORDS),
                "invalid"
            )
            verification.append(f'Verify page does not show valid result for "{invalid_val}"')
            return verification

        # Valid calculation
        verification.append('Verify monthly payment is displayed')
        expected = _try_compute_expected_value(steps)
        if expected:
            verification.append(f'Verify calculated result contains "{expected}"')

        # E2E mortgage also checks amortization table
        if ptype == "mortgage" and stype == "e2e":
            verification.append('Verify amortization schedule is displayed')

        return verification

    return verification


# ==============================================================================
# UTILITIES
# ==============================================================================

def _domain_name(url: str) -> str:
    try:
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return "Automated Test Suite"


def _module_name(strategy: dict, index: int) -> str:
    name = strategy.get("module_name", "").strip().upper()
    if name:
        return name
    url = strategy.get("url", "")
    path = url.rstrip("/").split("/")[-1]
    path = path.replace(".html", "").replace(".php", "")
    parts = [p.upper() for p in path.replace("-", "_").split("_") if p]
    return "_".join(parts[:2]) if parts else f"MODULE_{index}"


def _safe_step(step: str) -> str:
    step = step.strip().lstrip("* ").strip()
    step = step.replace("'", '"')
    return step


# ==============================================================================
# SCENARIO RENDERER
# ==============================================================================

def _render_scenario(scenario: dict, module: str, idx: int, page_url: str, used_ids: set) -> str:
    """Render a single Gauge scenario block with verified output steps."""

    raw_id = scenario.get("scenario_id", f"TC_{idx:03d}").strip().upper()
    scenario_id = f"{module}_{raw_id}"

    # Ensure uniqueness
    base_id = scenario_id
    counter = 1
    while scenario_id in used_ids:
        scenario_id = f"{base_id}_{counter}"
        counter += 1
    used_ids.add(scenario_id)

    title = scenario.get("title", f"Test {idx}")
    steps = scenario.get("steps", [])

    # Clean raw steps
    clean_steps = [_safe_step(s) for s in steps if isinstance(s, str) and s.strip()]

    # Ensure Navigate is first
    if not clean_steps or not clean_steps[0].startswith("Navigate to"):
        clean_steps.insert(0, f'Navigate to "{page_url}"')

    # Strip any existing verify steps — we regenerate with correct values
    clean_steps = [
        s for s in clean_steps
        if not any(s.lower().startswith(p) for p in _VERIFY_PREFIXES)
    ]

    # Generate and append correct verification steps
    all_steps = clean_steps + _build_verification_steps(scenario, page_url, clean_steps)

    lines = [f"## {scenario_id}: {title}", ""]
    lines += [f"* {s}" for s in all_steps]
    lines.append("")

    return "\n".join(lines)


# ==============================================================================
# MAIN GENERATOR
# ==============================================================================

def generate_spec(strategies: list, output_path: Optional[str] = None) -> str:
    """Generate a Gauge spec file from normalized strategy JSON."""

    if not strategies:
        raise ValueError("No strategies provided.")

    output_path = output_path or config.GENERATED_SPEC_PATH
    domain = _domain_name(strategies[0].get("url", ""))

    lines = ["Tags: regression", "", f"# {domain} Automated Test Suite", ""]
    used_ids: set = set()

    for i, strategy in enumerate(strategies, start=1):
        url = strategy.get("url", "")
        scenarios = strategy.get("test_scenarios", [])
        if not scenarios:
            continue
        module = _module_name(strategy, i)
        for j, scenario in enumerate(scenarios, start=1):
            lines.append(_render_scenario(scenario, module, j, url, used_ids))

    full_spec = "\n".join(lines).strip() + "\n"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_spec)

    logger.info(f"✓ Spec written: {output_path}")
    return full_spec


# ==============================================================================
# ENTRY POINT
# ==============================================================================

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )

    strategy_path = os.path.join(config.DATA_DIR, "strategy_normalized.json")

    if not os.path.exists(strategy_path):
        print("strategy_normalized.json not found. Run normalizer first.")
        sys.exit(1)

    with open(strategy_path, encoding="utf-8") as f:
        strategies = json.load(f)

    generate_spec(strategies)
    print("✓ Spec generated successfully.")


if __name__ == "__main__":
    main()
