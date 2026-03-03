"""
spec_generator.py
=================
Reads an AI-generated JSON file (from intelligence_layer/json_store/)
and converts it into a valid Gauge .spec file inside execution_layer/specs/.

Usage (standalone):
    python spec_generator.py --report_id 20240101_120000_abc12345
    python spec_generator.py --json_path path/to/custom.json

Also imported and called directly by gauge_runner.py.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# ── Default paths ─────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
JSON_STORE = BASE_DIR / "intelligence_layer" / "json_store"
SPECS_DIR  = BASE_DIR / "execution_layer" / "specs"

SPECS_DIR.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _safe_title(text: str, max_len: int = 60) -> str:
    """Strip Gauge-unsafe characters and truncate."""
    cleaned = re.sub(r"[^\w\s\-]", "", text).strip()
    return cleaned[:max_len] if cleaned else "Untitled Test"


def _to_step_line(raw: str) -> str:
    """
    Convert a natural-language step string into a Gauge step line.
    e.g.  '1. Click the Login button'  ->  '* Click the Login button'
          '- Enter email in field'      ->  '* Enter email in field'
    """
    cleaned = re.sub(r"^[\d]+[\.\)]\s*", "", raw.strip())   # remove leading numbers
    cleaned = re.sub(r"^[-*\u2022]\s*", "", cleaned)         # remove leading bullets
    return f"* {cleaned.rstrip('.')}"


def _step_semantic(step_text: str) -> str:
    """Classify a step into a broad semantic bucket."""
    lower = step_text.lower()
    if any(w in lower for w in ["navigate", "open", "go to", "visit", "load", "browse"]):
        return "navigation"
    if any(w in lower for w in ["click", "press", "tap", "select", "choose", "toggle"]):
        return "interaction"
    if any(w in lower for w in ["enter", "type", "fill", "input", "clear", "write"]):
        return "input"
    if any(w in lower for w in ["verify", "assert", "check", "confirm",
                                  "expect", "should", "must", "validate", "ensure"]):
        return "assertion"
    if any(w in lower for w in ["wait", "pause", "sleep", "idle"]):
        return "wait"
    if any(w in lower for w in ["screenshot", "capture", "snap", "photo"]):
        return "screenshot"
    if any(w in lower for w in ["scroll", "drag", "hover", "focus"]):
        return "gesture"
    return "action"


# ─────────────────────────────────────────────────────────────────────────────
# Core class
# ─────────────────────────────────────────────────────────────────────────────

class SpecGenerator:
    """
    Converts a JSON test-case document into a Gauge .spec file.

    Expected JSON structure
    -----------------------
    {
      "report_id": "20240101_120000_abc12345",
      "url": "https://target-app.com",
      "timestamp": "20240101_120000",
      "dom_data": { ... },          # optional, used for context comment
      "test_cases": [
        {
          "title":    "Login with valid credentials",
          "category": "functional",
          "steps":    ["Navigate to /login", "Enter admin in email field", ...],
          "expected": "User is redirected to dashboard"
        },
        ...
      ]
    }
    """

    def __init__(self, json_path: Path, output_dir: Path = SPECS_DIR):
        self.json_path  = json_path
        self.output_dir = output_dir
        self.data: dict = {}

    # ── Public ────────────────────────────────────────────────────────────────

    def generate(self) -> Path:
        """Load JSON → build spec text → write .spec file → return path."""
        self._load()
        spec_text = self._build_spec()
        spec_path = self._write(spec_text)
        print(f"[SpecGenerator] Written -> {spec_path}")
        return spec_path

    # ── Private ───────────────────────────────────────────────────────────────

    def _load(self):
        if not self.json_path.exists():
            raise FileNotFoundError(f"JSON not found: {self.json_path}")
        self.data = json.loads(self.json_path.read_text(encoding="utf-8"))
        if "test_cases" not in self.data:
            raise ValueError("JSON must contain a 'test_cases' key.")

    def _build_spec(self) -> str:
        report_id  = self.data.get("report_id", "unknown")
        url        = self.data.get("url", "unknown")
        timestamp  = self.data.get("timestamp",
                                   datetime.now().strftime("%Y%m%d_%H%M%S"))
        test_cases = self.data.get("test_cases", [])
        dom_data   = self.data.get("dom_data", {})

        lines: list[str] = []

        # ── Spec-level header ─────────────────────────────────────────────────
        lines += [
            "# AI Exploratory Tests",
            "",
            f"Report ID  : {report_id}",
            f"Target URL : {url}",
            f"Generated  : {timestamp}",
            f"Test Count : {len(test_cases)}",
        ]

        # Optional DOM context comment
        if dom_data:
            forms   = len(dom_data.get("forms", []))
            buttons = len(dom_data.get("buttons", []))
            inputs  = len(dom_data.get("inputs", []))
            links   = len(dom_data.get("links", []))
            lines.append(
                f"DOM Summary: {forms} forms, {inputs} inputs, "
                f"{buttons} buttons, {links} links"
            )

        lines.append("")

        # ── Spec-level tags ───────────────────────────────────────────────────
        categories = sorted({tc.get("category", "exploratory")
                              for tc in test_cases})
        lines += [f"tags: {', '.join(categories)}", ""]

        # ── Suite setup scenario ──────────────────────────────────────────────
        lines += [
            "## Suite Setup",
            "tags: setup",
            "",
            "* Open browser and navigate to base URL",
            "* Take a screenshot",
            "",
        ]

        # ── One scenario per test case ────────────────────────────────────────
        for idx, tc in enumerate(test_cases, 1):
            title    = _safe_title(tc.get("title", f"Test Case {idx}"))
            category = tc.get("category", "exploratory")
            steps    = tc.get("steps", [])
            expected = tc.get("expected", "")

            lines += [
                f"## {idx}. {title}",
                f"tags: {category}",
                "",
            ]

            prev_semantic = None
            for raw_step in steps:
                semantic = _step_semantic(raw_step)

                # Insert blank line before assertion block for readability
                if prev_semantic and prev_semantic != "assertion" and semantic == "assertion":
                    lines.append("")

                lines.append(_to_step_line(raw_step))
                prev_semantic = semantic

            # Expected result becomes the final assertion step
            if expected:
                lines += ["", _to_step_line(f"Verify: {expected}")]

            # Every scenario ends with a screenshot
            lines += ["* Take a screenshot", ""]

        # ── Suite teardown scenario ───────────────────────────────────────────
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
        description="Convert AI-generated JSON test cases to a Gauge .spec file."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--report_id",
        help="Report ID (filename without .json) inside intelligence_layer/json_store/",
    )
    group.add_argument(
        "--json_path",
        help="Explicit path to the JSON test-case file.",
    )
    parser.add_argument(
        "--output_dir",
        default=str(SPECS_DIR),
        help=f"Directory to write the .spec file (default: {SPECS_DIR})",
    )
    args = parser.parse_args()

    json_path = (
        Path(args.json_path)
        if args.json_path
        else JSON_STORE / f"{args.report_id}.json"
    )
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