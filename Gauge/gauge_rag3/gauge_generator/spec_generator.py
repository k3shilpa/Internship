"""
gauge_generator/spec_generator.py
===================================
Reads testcases.json and writes Gauge .spec files.

HOW TO RUN (from project root):
    python gauge_generator/spec_generator.py

ALL SETTINGS ARE HARDCODED BELOW — edit and run.
No config file, no CLI arguments, no relative imports.

testcases.json structure (output of ai_engine/test_generator.py):
  {
    "generation_metadata": { "base_url": "...", "generated_at": "...", ... },
    "statistics": { "by_category": {...}, "by_priority": {...}, "total": N },
    "test_cases": [
      {
        "id": "TC_001",
        "name": "...",
        "category": "functional",          # may be "functional|navigation" etc.
        "priority": "high" | "medium" | "low",
        "description": "...",
        "preconditions": ["..."],
        "steps": [
          {
            "step_number": 1,
            "action": "navigate" | "click" | "type" | "verify" | "assert_text" | ...,
            "target": {
              "element_type": "page" | "input" | "button" | "link" | "heading" | ...,
              "selector_type": "css" | "id" | "xpath" | "name" | "link_text",
              "selector_value": "...",
              "description": "..."
            },
            "input_data": "value" | null,
            "expected_result": "..."
          }
        ],
        "expected_outcome": "...",
        "tags": ["smoke", ...]
      }
    ]
  }
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
SPECS_OUTPUT_DIR = "specs"                             # where to write .spec files

ONLY_CATEGORY    = None    # None = all categories. e.g. "functional" for one only

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

    logger.info(f"  base_url : {base_url}")
    logger.info(f"  total    : {len(tcs)} test cases loaded")

    if ONLY_CATEGORY:
        # category field may be "functional|navigation" — match if token present
        tcs = [tc for tc in tcs if ONLY_CATEGORY in tc.get("category", "").split("|")]
        logger.info(f"  category filter: '{ONLY_CATEGORY}' -> {len(tcs)} tests")

    # Normalise compound categories ("functional|form") to their primary token
    for tc in tcs:
        tc["_primary_category"] = tc.get("category", "functional").split("|")[0].strip()

    grouped = {}
    for tc in tcs:
        grouped.setdefault(tc["_primary_category"], []).append(tc)

    created = []
    for cat, cases in sorted(grouped.items()):
        path = _write_spec(cat, cases, base_url)
        created.append(path)
        logger.info(f"  {path}  ({len(cases)} scenarios)")

    # Smoke spec — high-priority TCs, capped at 10
    high  = [tc for tc in tcs if tc.get("priority") == "high"][:10] or tcs[:5]
    smoke = _write_smoke(high, base_url)
    created.append(smoke)
    logger.info(f"  {smoke}  ({len(high)} smoke scenarios)")

    logger.info(f"\nDone — {len(created)} spec files written")
    logger.info(f"Next step: python gauge_generator/step_impl_generator.py")


# =============================================================================
#  SPEC FILE WRITERS
# =============================================================================

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


# =============================================================================
#  SCENARIO BUILDER
# =============================================================================

def _scenario(tc):
    tc_id = tc.get("id", "TC_000")
    lines = [f"## {tc.get('name', 'Unnamed Test')} [{tc_id}]", ""]

    # Tags: merge tc.tags + priority + id, deduplicated
    tags = list(tc.get("tags", []))
    for t in [tc.get("priority", "medium"), tc_id]:
        if t not in tags:
            tags.append(t)
    lines.append(f"tags: {', '.join(tags)}")
    lines.append("")

    # Preconditions as a comment block
    pres = tc.get("preconditions", [])
    if pres:
        lines.append(f"<!-- Pre: {'; '.join(pres)} -->")
        lines.append("")

    # Steps — sorted by step_number in case AI emitted them out of order
    steps = sorted(tc.get("steps", []), key=lambda s: s.get("step_number", 0))
    for step in steps:
        gauge_step = _step(step)
        if gauge_step:
            lines.append(f"* {gauge_step}")

    # Final verify step from expected_outcome
    outcome = tc.get("expected_outcome", "")
    if outcome:
        lines.append(f"* Verify test outcome is \"{_safe(outcome[:80])}\"")

    return lines


# =============================================================================
#  STEP TRANSLATOR
# =============================================================================

def _step(step):
    """
    Translates one structured step dict into a Gauge step string.

    Handles all action types the AI test generator produces:
      navigate, click, type, verify, assert_text, assert_visible,
      assert_url, select, hover, wait, scroll, clear
    """
    action = step.get("action", "verify")
    t      = step.get("target", {})

    st  = t.get("selector_type",  "css")      # id | css | xpath | name | link_text
    sv  = _q(t.get("selector_value", ""))     # the actual selector / URL
    et  = t.get("element_type",   "element")  # page | input | button | link | heading ...
    desc = t.get("description", "")

    inp = _q(step.get("input_data") or "")    # typed value (may be empty string)
    exp = _q((step.get("expected_result") or "")[:80])

    # ── navigate ─────────────────────────────────────────────────────────────
    if action == "navigate":
        return f"Navigate to url \"{sv}\""

    # ── click ─────────────────────────────────────────────────────────────────
    if action == "click":
        if st == "link_text":
            return f"Click on link with text \"{sv}\""
        if et in ("button", "input_button"):
            return f"Click on button with {st} \"{sv}\""
        if et == "link":
            return f"Click on link with {st} \"{sv}\""
        return f"Click on {et} with {st} \"{sv}\""

    # ── type / enter ──────────────────────────────────────────────────────────
    if action in ("type", "enter"):
        if inp == "":
            return f"Clear field with {st} \"{sv}\""
        return f"Enter \"{inp}\" in {et} with {st} \"{sv}\""

    # ── verify ────────────────────────────────────────────────────────────────
    if action == "verify":
        if et == "heading":
            return f"Verify heading with {st} \"{sv}\" contains \"{exp}\""
        if et == "title":
            return f"Verify page title is \"{exp}\""
        if et in ("page", "result", "error"):
            return f"Verify \"{exp}\" is displayed"
        return f"Verify element with {st} \"{sv}\" is visible"

    # ── assert variants ───────────────────────────────────────────────────────
    if action == "assert_text":
        return f"Assert text \"{inp or exp}\" exists on page"

    if action == "assert_visible":
        return f"Assert element with {st} \"{sv}\" is visible"

    if action == "assert_url":
        return f"Assert current URL contains \"{sv}\""

    # ── select ────────────────────────────────────────────────────────────────
    if action == "select":
        return f"Select option \"{inp}\" from dropdown with {st} \"{sv}\""

    # ── misc ─────────────────────────────────────────────────────────────────
    if action == "hover":
        return f"Hover over element with {st} \"{sv}\""
    if action == "wait":
        return f"Wait for element with {st} \"{sv}\" to be visible"
    if action == "scroll":
        return f"Scroll to element with {st} \"{sv}\""
    if action == "clear":
        return f"Clear field with {st} \"{sv}\""

    # ── fallback ──────────────────────────────────────────────────────────────
    return f"Perform {action} on \"{sv}\""


# =============================================================================
#  HELPERS
# =============================================================================

def _q(text):
    """Make a value safe for Gauge — strip angle brackets and quotes."""
    if text is None:
        return ""
    return str(text).replace("<", "").replace(">", "").replace('"', "'").strip()


def _safe(text):
    return str(text).replace("<", "").replace(">", "").replace('"', "'").strip()


if __name__ == "__main__":
    run()