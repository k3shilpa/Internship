"""
gauge_generator/spec_generator.py
===================================
Reads testcases.json and writes Gauge .spec files.

HOW TO RUN (from project root):
    python gauge_generator/spec_generator.py

ALL SETTINGS ARE HARDCODED BELOW — edit and run.
No config file, no CLI arguments, no relative imports.
"""

import json
import logging
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# =============================================================================
#  SETTINGS — edit these values directly
# =============================================================================

TESTCASES_FILE   = "data/testcases/testcases.json"    # from test_generator.py
SPECS_OUTPUT_DIR = "specs"              # where to write .spec files

ONLY_CATEGORY    = None    # None = all categories. e.g. "form" for one category only

# =============================================================================

os.makedirs(SPECS_OUTPUT_DIR, exist_ok=True)


def run():
    logger.info(f"\n{'='*55}")
    logger.info(f"SPEC GENERATOR")
    logger.info(f"  input  : {TESTCASES_FILE}")
    logger.info(f"  output : {SPECS_OUTPUT_DIR}")
    logger.info(f"{'='*55}")

    if not os.path.isfile(TESTCASES_FILE):
        raise FileNotFoundError(
            f"File not found: {TESTCASES_FILE}\n"
            f"Run ai_engine/test_generator.py first."
        )

    with open(TESTCASES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    tcs      = data.get("test_cases", [])
    base_url = data.get("generation_metadata", {}).get("base_url", "unknown")

    if ONLY_CATEGORY:
        tcs = [tc for tc in tcs if tc.get("category") == ONLY_CATEGORY]
        logger.info(f"  category filter: '{ONLY_CATEGORY}' -> {len(tcs)} tests")

    grouped = {}
    for tc in tcs:
        grouped.setdefault(tc.get("category", "functional"), []).append(tc)

    created = []
    for cat, cases in grouped.items():
        path = _write_spec(cat, cases, base_url)
        created.append(path)
        logger.info(f"  {path}  ({len(cases)} scenarios)")

    # Smoke spec
    high  = [tc for tc in tcs if tc.get("priority") == "high"][:10] or tcs[:5]
    smoke = _write_smoke(high, base_url)
    created.append(smoke)
    logger.info(f"  {smoke}  ({len(high)} smoke scenarios)")

    logger.info(f"\nDone — {len(created)} spec files written")
    logger.info(f"\nNext step: python gauge_generator/step_impl_generator.py")


def _write_spec(category, tcs, base_url):
    path  = os.path.join(SPECS_OUTPUT_DIR, f"{category}_tests.spec")
    lines = [
        f"# {category.replace('_', ' ').title()} Tests", "",
        f"Generated : {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Base URL  : {base_url}",
        f"Scenarios : {len(tcs)}", "",
        f"tags: {category}, automated", "",
    ]
    for tc in tcs:
        lines.extend(_scenario(tc))
        lines.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


def _write_smoke(tcs, base_url):
    path  = os.path.join(SPECS_OUTPUT_DIR, "smoke_tests.spec")
    lines = [
        "# Smoke Tests — High Priority", "",
        f"Generated : {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Base URL  : {base_url}", "",
        "tags: smoke, high-priority, automated", "",
    ]
    for tc in tcs:
        lines.extend(_scenario(tc))
        lines.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


def _scenario(tc):
    tc_id = tc.get("id", "TC_000")
    lines = [f"## {tc.get('name', 'Unnamed Test')} [{tc_id}]", ""]
    tags  = list(tc.get("tags", []))
    for t in [tc.get("priority", "medium"), tc_id]:
        if t not in tags:
            tags.append(t)
    lines.append(f"tags: {', '.join(tags)}")
    lines.append("")
    pres = tc.get("preconditions", [])
    if pres:
        lines.append(f"<!-- Pre: {'; '.join(pres)} -->")
        lines.append("")
    for step in tc.get("steps", []):
        lines.append(f"* {_step(step)}")
    outcome = tc.get("expected_outcome", "")
    if outcome:
        lines.append(f"* Verify test outcome is \"{_safe(outcome[:80])}\"")
    return lines


def _step(step):
    action = step.get("action", "verify")
    t      = step.get("target", {})
    st     = t.get("selector_type",  "css")
    sv     = _q(t.get("selector_value", "body"))   # quoted selector value
    et     = t.get("element_type",   "element")
    inp    = _q(step.get("input_data") or "value")  # quoted input value
    exp    = _q((step.get("expected_result") or "")[:40])
    MAP = {
        "navigate":       f"Navigate to url \"{sv}\"",
        "click":          f"Click on {et} with {st} \"{sv}\"",
        "type":           f"Enter \"{inp}\" in {et} with {st} \"{sv}\"",
        "verify":         f"Verify element with {st} \"{sv}\" is visible",
        "assert_text":    f"Assert text \"{inp}\" exists on page",
        "assert_visible": f"Assert element with {st} \"{sv}\" is visible",
        "assert_url":     f"Assert current URL contains \"{inp}\"",
        "select":         f"Select option \"{inp}\" from dropdown with {st} \"{sv}\"",
        "hover":          f"Hover over element with {st} \"{sv}\"",
        "wait":           f"Wait for element with {st} \"{sv}\" to be visible",
        "scroll":         f"Scroll to element with {st} \"{sv}\"",
        "clear":          f"Clear field with {st} \"{sv}\"",
    }
    return MAP.get(action, f"Perform {action} on \"{sv}\"")


def _q(text):
    """Make a value safe for Gauge — strip angle brackets and quotes."""
    if text is None:
        return "value"
    return str(text).replace("<", "").replace(">", "").replace('"', "'").strip()


def _safe(text):
    return str(text).replace("<", "").replace(">", "").replace('"', "'").strip()


if __name__ == "__main__":
    run()