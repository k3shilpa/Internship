"""
spec_generator.py  [FIXED — direct passthrough, no translation layer]
======================================================================
Converts AI JSON test cases into a valid Gauge .spec file.

KEY RULE: The AI prompt (testcase_generator.py) is responsible for producing
steps that EXACTLY match a @step in ai_steps.py. This file writes them
directly — no translation, no regex guessing.

Gauge parameter matching:
  @step("Enter <text> in <field>")  matches  "* Enter foo in bar"
  @step("Click button <label>")     matches  "* Click button Search"
  @step("Verify: <assertion>")      matches  "* Verify: anything here"
  @step("Perform action <desc>")    matches  "* Perform action anything"
"""

from __future__ import annotations
import argparse, json, re, sys
from datetime import datetime
from pathlib import Path

BASE_DIR   = Path(__file__).parent
JSON_STORE = BASE_DIR / "intelligence_layer" / "json_store"
SPECS_DIR  = BASE_DIR / "execution_layer" / "specs"
SPECS_DIR.mkdir(parents=True, exist_ok=True)


# ── Known step patterns (mirrors every @step in ai_steps.py) ────────────────

KNOWN_PATTERNS = [
    r"^Open browser and navigate to base URL$",
    r"^Navigate to .+$",
    r"^Refresh the page$",
    r"^Go back to previous page$",
    r"^Go forward to next page$",
    r"^Click button .+$",
    r"^Click link .+$",
    r"^Click on .+$",
    r"^Click on a navigation link$",
    r"^Click on forgot password link$",
    r"^Double click on .+$",
    r"^Right click on .+$",
    r"^Hover over .+$",
    r"^Enter .+ in .+$",
    r"^Type .+ in .+$",
    r"^Clear field .+$",
    r"^Select .+ from .+$",
    r"^Check checkbox .+$",
    r"^Uncheck checkbox .+$",
    r"^Upload file .+ to .+$",
    r"^Press key .+$",
    r"^Enter a sql injection string in the login form$",
    r"^Submit the form$",
    r"^Scroll down$",
    r"^Scroll up$",
    r"^Scroll to .+$",
    r"^Focus on .+$",
    r"^Drag .+ and drop on .+$",
    r"^Verify: .+$",
    r"^Verify page title contains .+$",
    r"^Verify text .+ is visible$",
    r"^Verify text .+ is not visible$",
    r"^Verify element .+ is visible$",
    r"^Verify element .+ is hidden$",
    r"^Verify current URL contains .+$",
    r"^Verify input .+ has value .+$",
    r"^Wait for network idle$",
    r"^Wait for element .+$",
    r"^Wait .+ seconds$",
    r"^Take a screenshot$",
    r"^Log in with username .+ and password .+$",
    r"^Log out$",
    r"^Accept dialog$",
    r"^Dismiss dialog$",
    r"^Close modal$",
    r"^Switch to tab .+$",
    r"^Perform action .+$",
]


def _validate_step(step: str) -> str:
    """
    Warn if a step doesn't match any known @step pattern.
    Returns the step unchanged — never modifies or translates it.
    This is a diagnostic tool only; Gauge is the final authority.
    """
    if not any(re.match(p, step) for p in KNOWN_PATTERNS):
        print(f"[WARN] Unrecognised step (may fail Gauge validation): '{step}'")
    return step


def _sanitise_title(text: str) -> str:
    """Remove chars that cause Gauge ParseErrors in scenario headings."""
    text = re.sub(r"[<>\[\]{}|\\\"\']+", "", text)
    return text.strip()[:60]


def _sanitise_expected(text: str) -> str:
    """
    Clean the expected-result string for use inside a Verify: step.
    Converts <angle bracket tokens> to (parens) so Gauge does not
    treat them as dynamic parameters.
    """
    text = re.sub(r"<(/?\w[\w\s]*?)>", r"(\1)", text)
    text = text.replace("<", "(").replace(">", ")")
    text = text.replace('"', "'").replace("''", "'")
    return text.strip()[:120]


# ── Core generator ───────────────────────────────────────────────────────────

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
        timestamp  = self.data.get("timestamp",
                                   datetime.now().strftime("%Y%m%d_%H%M%S"))
        test_cases = self.data.get("test_cases", [])
        dom_data   = self.data.get("dom_data", {})

        lines: list[str] = []

        # ── File header ──────────────────────────────────────────────────────
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

        cats = sorted({tc.get("category", "exploratory") for tc in test_cases})
        lines += [f"tags: {', '.join(cats)}", ""]

        # ── Suite Setup ──────────────────────────────────────────────────────
        lines += [
            "## Suite Setup",
            "tags: setup",
            "",
            "* Open browser and navigate to base URL",
            "* Take a screenshot",
            "",
        ]

        # ── Test scenarios ───────────────────────────────────────────────────
        for idx, tc in enumerate(test_cases, 1):
            title    = _sanitise_title(tc.get("title", f"Test Case {idx}"))
            category = tc.get("category", "exploratory")
            priority = tc.get("priority", "medium")
            steps    = tc.get("steps", [])
            expected = tc.get("expected", "")

            lines += [f"## {idx}. {title}", f"tags: {category}, {priority}", ""]

            prev_verify = False
            for raw_step in steps:
                clean_step = raw_step.strip()
                if not clean_step:
                    continue

                # Write the step directly — no translation
                validated  = _validate_step(clean_step)
                is_verify  = validated.lower().startswith("verify")

                # Blank line before first verify in a group for readability
                if is_verify and not prev_verify:
                    lines.append("")

                lines.append("* " + validated)
                prev_verify = is_verify

            # Append the expected outcome as a final Verify step
            if expected:
                cleaned = _sanitise_expected(expected)
                if cleaned:
                    lines += ["", "* Verify: " + cleaned]

            lines += ["* Take a screenshot", ""]

        # ── Suite Teardown ───────────────────────────────────────────────────
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


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate a Gauge .spec file from an AI test-case JSON."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--report_id",
        help="Report ID matching a file in intelligence_layer/json_store/")
    group.add_argument("--json_path",
        help="Explicit path to the JSON file.")
    parser.add_argument("--output_dir", default=str(SPECS_DIR),
        help="Directory to write the .spec file into.")
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