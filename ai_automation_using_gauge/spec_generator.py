"""
spec_generator.py  [FIXED]
==========================
Converts AI-generated JSON test cases into a valid Gauge .spec file.

Key fixes:
  1. Every step written to the spec maps to a REAL @step in ai_steps.py.
     Free-form AI prose like "Open the web application in a browser" is
     translated using a smart mapping table.
  2. Angle brackets <...> and special chars are sanitised so Gauge does
     not throw ParseErrors.
  3. Windows paths use forward slashes.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR   = Path(__file__).parent
JSON_STORE = BASE_DIR / "intelligence_layer" / "json_store"
SPECS_DIR  = BASE_DIR / "execution_layer" / "specs"
SPECS_DIR.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# Sanitise text — remove chars that break Gauge spec parsing
# ─────────────────────────────────────────────────────────────────────────────

def _sanitise(text: str) -> str:
    text = re.sub(r"<(/?\w[\w\s]*?)>", r"(\1)", text)   # <script> -> (script)
    text = text.replace("<", "(").replace(">", ")")       # remaining < >
    text = text.replace("''", "'")
    text = text.replace('"', "'")
    return text.strip()


# ─────────────────────────────────────────────────────────────────────────────
# Translate free-form AI step → real Gauge step
# Every returned string is a valid "* Step text" that matches ai_steps.py
# ─────────────────────────────────────────────────────────────────────────────

def _translate(raw: str) -> str:
    lower = raw.lower()

    # ── Open browser / Navigate ───────────────────────────────────────────────
    if re.search(r"open.*(?:browser|app|web|site|application)|launch.*browser|"
                 r"start.*browser", lower):
        return "* Open browser and navigate to base URL"

    if re.search(r"navigate to|go to url|visit url", lower):
        m = re.search(r"(https?://\S+|/\w\S*)", raw)
        url = m.group(1) if m else "/"
        return f"* Navigate to {url}"

    if re.search(r"refresh|reload page", lower):
        return "* Refresh the page"

    if re.search(r"go back|previous page", lower):
        return "* Go back to previous page"

    # ── Scroll ────────────────────────────────────────────────────────────────
    if re.search(r"scroll down", lower):
        return "* Scroll down"

    if re.search(r"scroll up", lower):
        return "* Scroll up"

    # ── Specific click patterns ───────────────────────────────────────────────
    if re.search(r"click.*search bar|click.*search field", lower):
        return "* Click on search"

    if re.search(r"click.*(?:login|sign.?in).*button|click.*(?:the )?login$|"
                 r"click.*(?:the )?sign.?in$", lower):
        return "* Click button Login"

    if re.search(r"click.*search button|click.*the search$", lower):
        return "* Click button Search"

    if re.search(r"click.*submit button|click.*the submit$", lower):
        return "* Click button Submit"

    if re.search(r"click.*signup|click.*sign up|click.*register", lower):
        return "* Click button Sign Up"

    # Generic button click
    if re.search(r"click.*button", lower):
        m = re.search(r"click (?:on )?(?:the )?(.+?) button", lower)
        label = _sanitise(m.group(1)).strip().title()[:40] if m else "Submit"
        return f"* Click button {label}"

    # Generic click
    if re.search(r"click|tap|press", lower):
        m = re.search(r"(?:click|tap|press) (?:on )?(?:the )?(.+?)$", lower)
        elem = _sanitise(m.group(1)).strip()[:40] if m else "element"
        return f"* Click on {elem}"

    # ── Input — empty / no entry ──────────────────────────────────────────────
    if re.search(r"do not enter|leave.*(?:empty|blank)|without.*(?:entering|input)|"
                 r"no.*(?:data|input|query)", lower):
        return "* Submit the form"

    # ── Input — specific patterns ─────────────────────────────────────────────
    if re.search(r"enter.*valid.*username.*password|enter.*credentials", lower):
        return "* Enter testuser in username"

    if re.search(r"enter.*(?:wrong|invalid|incorrect).*password", lower):
        return "* Enter wrongpassword in password"

    if re.search(r"enter.*single char", lower):
        return "* Enter a in search"

    if re.search(r"boundary value|min.*max|numeric range", lower):
        return "* Enter 99999 in input"

    if re.search(r"xss|script.*alert|injection probe", lower):
        return "* Enter xss-test-payload in input"

    if re.search(r"special char|special.*characters", lower):
        return "* Enter !@#special in search"

    if re.search(r"enter.*query|type.*query|enter.*search term|enter.*keyword", lower):
        return "* Enter test-query in search"

    if re.search(r"enter|type|fill|input", lower):
        m = re.search(r"(?:enter|type|fill|input)\s+(.+?)\s+(?:in|into)\s+(.+?)$", lower)
        if m:
            text  = _sanitise(m.group(1))[:30]
            field = _sanitise(m.group(2))[:30]
            return f"* Enter {text} in {field}"
        return "* Enter test-value in input"

    # ── Submit ────────────────────────────────────────────────────────────────
    if re.search(r"submit.*form|submit the", lower):
        return "* Submit the form"

    # ── Verify / Assert ───────────────────────────────────────────────────────
    if re.search(r"verify|assert|check|confirm|ensure|should|must|validate|expect", lower):
        clean = re.sub(
            r"^(verify|assert|check|confirm|ensure|validate)[:\s]+(?:that\s+)?",
            "", raw, flags=re.IGNORECASE
        ).strip()
        clean = _sanitise(clean)[:120] if clean else _sanitise(raw)[:120]
        return f"* Verify: {clean}"

    # ── Hover ─────────────────────────────────────────────────────────────────
    if re.search(r"hover", lower):
        m = re.search(r"hover over (.+?)$", lower)
        elem = _sanitise(m.group(1))[:40] if m else "element"
        return f"* Hover over {elem}"

    # ── Wait ──────────────────────────────────────────────────────────────────
    if re.search(r"wait|network idle|page.*load", lower):
        return "* Wait for network idle"

    # ── Screenshot ────────────────────────────────────────────────────────────
    if re.search(r"screenshot|capture|snap", lower):
        return "* Take a screenshot"

    # ── Generic fallback ──────────────────────────────────────────────────────
    clean = _sanitise(raw)[:80]
    return f"* Perform action {clean}"


# ─────────────────────────────────────────────────────────────────────────────
# Core generator
# ─────────────────────────────────────────────────────────────────────────────

class SpecGenerator:

    def __init__(self, json_path: Path, output_dir: Path = SPECS_DIR):
        self.json_path  = json_path
        self.output_dir = output_dir
        self.data: dict = {}

    def generate(self) -> Path:
        self._load()
        spec_text = self._build()
        spec_path = self._write(spec_text)
        print(f"[SpecGenerator] Written -> {spec_path}")
        return spec_path

    def _load(self):
        if not self.json_path.exists():
            raise FileNotFoundError(f"JSON not found: {self.json_path}")
        self.data = json.loads(self.json_path.read_text(encoding="utf-8"))
        if "test_cases" not in self.data:
            raise ValueError("JSON must contain 'test_cases'")

    def _build(self) -> str:
        report_id  = self.data.get("report_id", "unknown")
        url        = self.data.get("url", "unknown")
        timestamp  = self.data.get("timestamp", datetime.now().strftime("%Y%m%d_%H%M%S"))
        test_cases = self.data.get("test_cases", [])
        dom_data   = self.data.get("dom_data", {})

        lines: list[str] = []

        lines += [
            "# AI Exploratory Tests",
            "",
            f"Report ID  : {report_id}",
            f"Target URL : {url}",
            f"Generated  : {timestamp}",
            f"Test Count : {len(test_cases)}",
        ]
        if dom_data:
            lines.append(
                f"DOM Summary: {len(dom_data.get('forms', []))} forms, "
                f"{len(dom_data.get('inputs', []))} inputs, "
                f"{len(dom_data.get('buttons', []))} buttons, "
                f"{len(dom_data.get('links', []))} links"
            )
        lines.append("")

        categories = sorted({tc.get("category", "exploratory") for tc in test_cases})
        lines += [f"tags: {', '.join(categories)}", ""]

        # Suite Setup
        lines += [
            "## Suite Setup",
            "tags: setup",
            "",
            "* Open browser and navigate to base URL",
            "* Take a screenshot",
            "",
        ]

        # One scenario per test case
        for idx, tc in enumerate(test_cases, 1):
            raw_title = tc.get("title", f"Test Case {idx}")
            title     = re.sub(r"[<>\[\]{}|\\\"']", "", raw_title).strip()[:60]
            category  = tc.get("category", "exploratory")
            steps     = tc.get("steps", [])
            expected  = tc.get("expected", "")

            lines += [
                f"## {idx}. {title}",
                f"tags: {category}",
                "",
            ]

            prev_was_verify = False
            for raw_step in steps:
                translated = _translate(raw_step)
                is_verify  = translated.startswith("* Verify")

                if is_verify and not prev_was_verify:
                    lines.append("")   # blank line before assertion block

                lines.append(translated)
                prev_was_verify = is_verify

            if expected:
                clean = _sanitise(expected)[:120]
                lines += ["", f"* Verify: {clean}"]

            lines += ["* Take a screenshot", ""]

        # Suite Teardown
        lines += [
            "## Suite Teardown",
            "tags: teardown",
            "",
            "* Wait for network idle",
            "* Take a screenshot",
            "",
        ]

        return "\n".join(lines)

    def _write(self, spec_text: str) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        report_id = self.data.get("report_id", "run")
        spec_path = self.output_dir / f"{report_id}.spec"
        spec_path.write_text(spec_text, encoding="utf-8")
        return spec_path


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Convert AI JSON test cases to a Gauge .spec file."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--report_id")
    group.add_argument("--json_path")
    parser.add_argument("--output_dir", default=str(SPECS_DIR))
    args = parser.parse_args()

    json_path  = (Path(args.json_path) if args.json_path
                  else JSON_STORE / f"{args.report_id}.json")
    output_dir = Path(args.output_dir)

    try:
        spec_path = SpecGenerator(json_path, output_dir).generate()
        print(f"[OK] {spec_path}")
        sys.exit(0)
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()