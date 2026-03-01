"""
step_generator.py
=================
Parses Gauge .spec files and auto-generates step_impl/step_impl.py
with Selenium implementations for every unique step found.

Usage:
    python step_generator.py                        # scans ./specs folder
    python step_generator.py --specs path/to/specs  # custom specs folder
    python step_generator.py --specs a.spec b.spec  # specific files

Output:
    step_impl/step_impl.py
"""

import os
import re
import sys
import argparse
import textwrap
from pathlib import Path


# ---------------------------------------------------------------------------
# Step pattern registry
# Each entry: (regex_to_match_step, function_name, param_names, code_body)
# ---------------------------------------------------------------------------

STEP_PATTERNS = [
    # Navigate
    (
        r'^navigate to url "([^"]+)"$',
        "navigate_to_url",
        ["url"],
        'driver.get(url)\nMessages.write_message(f"Navigated to: {url}")',
    ),
    # Verify heading xpath
    (
        r'^verify heading with xpath "([^"]+)" contains "([^"]+)"$',
        "verify_heading_with_xpath",
        ["xpath", "expected_text"],
        textwrap.dedent("""\
            element = WebDriverWait(driver, WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            actual_text = element.text
            assert expected_text in actual_text, (
                f"Expected heading to contain '{expected_text}', but got '{actual_text}'"
            )
            Messages.write_message(f"Heading verified: '{actual_text}'")\
        """),
    ),
    # Verify test outcome
    (
        r'^verify test outcome is "([^"]+)"$',
        "verify_test_outcome",
        ["outcome"],
        'Messages.write_message(f"Expected outcome: {outcome}")',
    ),
    # Verify element visible by name
    (
        r'^verify element with name "([^"]+)" is visible$',
        "verify_element_with_name_is_visible",
        ["name"],
        textwrap.dedent("""\
            element = WebDriverWait(driver, WAIT_TIMEOUT).until(
                EC.visibility_of_element_located((By.NAME, name))
            )
            assert element.is_displayed(), f"Element name='{name}' is not visible"
            Messages.write_message(f"Element '{name}' is visible")\
        """),
    ),
    # Click link
    (
        r'^click on link with text "([^"]+)"$',
        "click_on_link_with_text",
        ["link_text"],
        textwrap.dedent("""\
            element = WebDriverWait(driver, WAIT_TIMEOUT).until(
                EC.element_to_be_clickable((By.LINK_TEXT, link_text))
            )
            element.click()
            Messages.write_message(f"Clicked link: '{link_text}'")\
        """),
    ),
    # Click button by name
    (
        r'^click on button with name "([^"]+)"$',
        "click_on_button_with_name",
        ["name"],
        textwrap.dedent("""\
            element = WebDriverWait(driver, WAIT_TIMEOUT).until(
                EC.element_to_be_clickable((By.NAME, name))
            )
            element.click()
            Messages.write_message(f"Clicked button name='{name}'")\
        """),
    ),
    # Enter value by ID
    (
        r'^enter "([^"]+)" in input with id "([^"]+)"$',
        "enter_value_in_input_with_id",
        ["value", "field_id"],
        textwrap.dedent("""\
            element = WebDriverWait(driver, WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.ID, field_id))
            )
            element.clear()
            element.send_keys(value)
            Messages.write_message(f"Entered '{value}' in input id='{field_id}'")\
        """),
    ),
    # Clear by ID
    (
        r'^clear field with id "([^"]+)"$',
        "clear_field_with_id",
        ["field_id"],
        textwrap.dedent("""\
            element = WebDriverWait(driver, WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.ID, field_id))
            )
            element.clear()
            Messages.write_message(f"Cleared input id='{field_id}'")\
        """),
    ),
    # Enter value by NAME
    (
        r'^enter "([^"]+)" in input with name "([^"]+)"$',
        "enter_value_in_input_with_name",
        ["value", "field_name"],
        textwrap.dedent("""\
            element = WebDriverWait(driver, WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.NAME, field_name))
            )
            element.clear()
            element.send_keys(value)
            Messages.write_message(f"Entered '{value}' in input name='{field_name}'")\
        """),
    ),
    # Clear by NAME
    (
        r'^clear field with name "([^"]+)"$',
        "clear_field_with_name",
        ["field_name"],
        textwrap.dedent("""\
            element = WebDriverWait(driver, WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.NAME, field_name))
            )
            element.clear()
            Messages.write_message(f"Cleared input name='{field_name}'")\
        """),
    ),
]


# ---------------------------------------------------------------------------
# Parser: extract raw step strings from spec files
# ---------------------------------------------------------------------------

def extract_steps_from_spec(spec_text: str) -> list[str]:
    """Return list of raw step strings (lines starting with *)."""
    steps = []
    for line in spec_text.splitlines():
        line = line.strip()
        if line.startswith("* "):
            steps.append(line[2:].strip())
    return steps


def collect_spec_files(paths: list[str]) -> list[Path]:
    """Resolve list of .spec files from given file/folder paths."""
    spec_files = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            spec_files.extend(path.rglob("*.spec"))
        elif path.is_file() and path.suffix == ".spec":
            spec_files.append(path)
        else:
            print(f"[WARN] Skipping '{p}' — not a .spec file or directory.")
    return spec_files


# ---------------------------------------------------------------------------
# Matcher: convert a raw step string to a Gauge template + matched pattern
# ---------------------------------------------------------------------------

def step_to_template(raw_step: str):
    """
    Replace literal quoted values in a step with <param> placeholders.
    Returns (gauge_step_template, matched_pattern_entry | None)
    """
    # Build gauge template by replacing "literal values" with <param>
    template = re.sub(r'"[^"]*"', lambda m: "<param>", raw_step)

    # Try to match against known patterns (case-insensitive)
    for pattern, fn_name, params, body in STEP_PATTERNS:
        if re.match(pattern, raw_step, re.IGNORECASE):
            # Build proper gauge template with named params
            gauge_template = re.sub(r'"[^"]*"', lambda m, it=iter(params): f'<{next(it)}>', raw_step)
            return gauge_template, (pattern, fn_name, params, body)

    return template, None   # unrecognized step


# ---------------------------------------------------------------------------
# Code generator
# ---------------------------------------------------------------------------

FILE_HEADER = '''\
"""
step_impl.py — Auto-generated by step_generator.py
Do NOT edit manually; re-run step_generator.py to regenerate.

Requirements:
    pip install getgauge selenium webdriver-manager
"""

from getgauge.python import step, before_scenario, after_scenario, Messages
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

driver = None
WAIT_TIMEOUT = 10


# ---------------------------------------------------------------------------
# Hooks
# ---------------------------------------------------------------------------

@before_scenario
def before_scenario_hook():
    global driver
    options = Options()
    options.add_argument("--start-maximized")
    # options.add_argument("--headless")   # uncomment for CI/headless runs
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(WAIT_TIMEOUT)


@after_scenario
def after_scenario_hook():
    global driver
    if driver:
        driver.quit()
        driver = None


# ---------------------------------------------------------------------------
# Generated Steps
# ---------------------------------------------------------------------------

'''


def make_fn_name(gauge_template: str, used_names: dict) -> str:
    """Derive a unique Python function name from the gauge step template."""
    # Strip param placeholders and non-alpha chars
    name = re.sub(r"<[^>]+>", "", gauge_template)
    name = re.sub(r"[^a-zA-Z0-9 ]", "", name)
    name = "_".join(name.lower().split())
    name = name[:60] or "step"
    # Ensure uniqueness
    base = name
    count = used_names.get(base, 0)
    used_names[base] = count + 1
    return base if count == 0 else f"{base}_{count}"


def indent_body(body: str) -> str:
    """Indent all lines of body with 4 spaces (for inside a function)."""
    lines = body.splitlines()
    return "\n".join("    " + line if line.strip() else "" for line in lines)


def generate_step_impl(unique_steps: list[tuple]) -> str:
    """
    unique_steps: list of (gauge_template, matched_pattern | None)
    Returns full file content as string.
    """
    used_names: dict = {}
    blocks = [FILE_HEADER]

    for gauge_template, match in unique_steps:
        if match:
            _, fn_name_base, params, body = match
            used_names[fn_name_base] = used_names.get(fn_name_base, 0) + 1
            fn_name = fn_name_base if used_names[fn_name_base] == 1 else f"{fn_name_base}_{used_names[fn_name_base]}"
            params_str = ", ".join(params)
            body_indented = indent_body(body)
            block = (
                f'@step("{gauge_template}")\n'
                f"def {fn_name}({params_str}):\n"
                f"{body_indented}\n"
                f"\n"
            )
            blocks.append(block)
        else:
            fn_name = make_fn_name(gauge_template, used_names)
            param_count = gauge_template.count("<param>")
            params_str = ", ".join(f"param{i+1}" for i in range(param_count))
            block = (
                f'@step("{gauge_template}")\n'
                f"def {fn_name}({params_str}):\n"
                f'    # TODO: No matching implementation found — implement manually\n'
                f'    raise NotImplementedError("Step not implemented: {gauge_template}")\n'
                f"\n"
            )
            blocks.append(block)

    return "\n".join(blocks)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Auto-generate Gauge step_impl.py from .spec files."
    )
    parser.add_argument(
        "--specs",
        nargs="+",
        default=["specs"],
        metavar="PATH",
        help="One or more .spec files or folders containing .spec files (default: ./specs)",
    )
    parser.add_argument(
        "--output",
        default="step_impl/step_impl.py",
        metavar="FILE",
        help="Output file path (default: step_impl/step_impl.py)",
    )
    args = parser.parse_args()

    # Collect spec files
    spec_files = collect_spec_files(args.specs)
    if not spec_files:
        print("[ERROR] No .spec files found. Check your --specs path.")
        sys.exit(1)

    print(f"[INFO] Found {len(spec_files)} spec file(s):")
    for sf in spec_files:
        print(f"       {sf}")

    # Extract all steps, deduplicate while preserving order
    seen_templates: dict = {}       # gauge_template -> match
    seen_raw: set = set()

    for spec_file in spec_files:
        text = spec_file.read_text(encoding="utf-8")
        raw_steps = extract_steps_from_spec(text)
        for raw in raw_steps:
            raw_lower = raw.lower()
            if raw_lower in seen_raw:
                continue
            seen_raw.add(raw_lower)
            gauge_template, match = step_to_template(raw)
            # Deduplicate by template
            if gauge_template not in seen_templates:
                seen_templates[gauge_template] = match

    unique_steps = list(seen_templates.items())
    print(f"[INFO] Unique steps found: {len(unique_steps)}")

    # Count recognized vs unknown
    recognized = sum(1 for _, m in unique_steps if m is not None)
    unknown = len(unique_steps) - recognized
    print(f"       Recognized : {recognized}")
    if unknown:
        print(f"       Unknown (TODO): {unknown}")

    # Generate code
    code = generate_step_impl(unique_steps)

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(code, encoding="utf-8")
    print(f"[OK]  Generated: {output_path.resolve()}")

    # Print unknown steps for awareness
    if unknown:
        print("\n[WARN] The following steps had no matching implementation and need manual coding:")
        for tmpl, match in unique_steps:
            if match is None:
                print(f"       * {tmpl}")


if __name__ == "__main__":
    main()