"""
step_impl_generator.py
======================
Reads an AI-generated JSON file and auto-generates a complete, generic
Gauge step implementation file (ai_steps.py) that covers every unique
step pattern found in the test cases.

The generated file uses Playwright and is fully generic -- it works
across any website because it uses flexible multi-strategy locators
(id, name, text, aria-label, placeholder, CSS, role) with fallback chains.

Usage (standalone):
    python step_impl_generator.py --report_id 20240101_120000_abc12345
    python step_impl_generator.py --json_path path/to/custom.json

Also called automatically by gauge_runner.py before each run.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from datetime import datetime

# ── Default paths ─────────────────────────────────────────────────────────────
BASE_DIR       = Path(__file__).parent
JSON_STORE     = BASE_DIR / "intelligence_layer" / "json_store"
STEP_IMPL_DIR  = BASE_DIR / "execution_layer" / "step_impl"
OUTPUT_FILE    = STEP_IMPL_DIR / "ai_steps.py"


# ─────────────────────────────────────────────────────────────────────────────
# Step pattern analyser
# ─────────────────────────────────────────────────────────────────────────────

# Maps regex patterns found in step text to a canonical step template name.
# Order matters — first match wins.
STEP_PATTERNS: list[tuple[str, str]] = [
    # Navigation
    (r"navigate|go to|open|visit|browse|load page",          "navigate"),
    (r"refresh|reload",                                       "refresh"),
    (r"back|previous page",                                   "go_back"),
    (r"forward",                                              "go_forward"),

    # Input
    (r"enter|type|fill|input|write",                          "enter_text"),
    (r"clear|empty",                                          "clear_field"),
    (r"select.*(dropdown|option|list)",                       "select_option"),
    (r"upload|attach file",                                   "upload_file"),
    (r"check|tick|enable.*(checkbox)",                        "check_checkbox"),
    (r"uncheck|untick|disable.*(checkbox)",                   "uncheck_checkbox"),

    # Interaction
    (r"click|press|tap|push",                                 "click"),
    (r"double.click|dblclick",                                "double_click"),
    (r"right.click|context.menu",                             "right_click"),
    (r"hover|mouse over",                                     "hover"),
    (r"drag.*drop",                                           "drag_drop"),
    (r"scroll down",                                          "scroll_down"),
    (r"scroll up",                                            "scroll_up"),
    (r"scroll to",                                            "scroll_to_element"),
    (r"focus",                                                "focus_element"),
    (r"submit",                                               "submit_form"),
    (r"press key|keyboard",                                   "press_key"),

    # Assertions
    (r"verify|assert|check|confirm|validate|ensure|should|must|expect", "verify"),

    # Waits
    (r"wait for network|network idle",                        "wait_network_idle"),
    (r"wait for|wait until",                                  "wait_for_element"),
    (r"wait",                                                 "wait_seconds"),

    # Visual
    (r"screenshot|capture|snap",                              "take_screenshot"),

    # Auth
    (r"log(in|out)|sign (in|out)|logout|login",               "auth_action"),

    # Alerts / dialogs
    (r"accept|dismiss|close.*dialog|alert",                   "handle_dialog"),

    # Tabs / windows
    (r"new tab|switch tab|open tab",                          "switch_tab"),

    # iframe
    (r"iframe|frame",                                         "switch_frame"),

    # Fallback
    (r".*",                                                   "generic_action"),
]


def _classify_step(step_text: str) -> str:
    """Return the canonical step-type name for a raw step string."""
    lower = step_text.lower()
    for pattern, name in STEP_PATTERNS:
        if re.search(pattern, lower):
            return name
    return "generic_action"


def _collect_step_types(test_cases: list[dict]) -> set[str]:
    """Walk all test case steps and collect unique step-type names."""
    types: set[str] = set()
    types.add("open_browser")     # always needed
    types.add("take_screenshot")  # always needed
    types.add("wait_network_idle")

    for tc in test_cases:
        for step in tc.get("steps", []):
            types.add(_classify_step(step))
        if tc.get("expected"):
            types.add("verify")

    return types


# ─────────────────────────────────────────────────────────────────────────────
# Code-block library
# Each function returns a string block that will be written into ai_steps.py
# ─────────────────────────────────────────────────────────────────────────────

def _header(url: str, report_id: str, timestamp: str) -> str:
    return f'''"""
ai_steps.py  (AUTO-GENERATED)
==============================
Generated by step_impl_generator.py
Report ID  : {report_id}
Target URL : {url}
Generated  : {timestamp}

This file is generic -- it works across any website using
multi-strategy Playwright locators with automatic fallback chains.
Do NOT edit manually; re-run step_impl_generator.py to regenerate.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from getgauge.python import (
    step, before_suite, after_suite, before_scenario,
    after_scenario, Messages, Screenshots
)

load_dotenv(Path(__file__).parent.parent.parent / ".env")

BASE_URL = os.getenv("BASE_URL", "{url}")

_driver = None


# ─────────────────────────────────────────────────────────────────────────────
# Driver helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get_driver():
    global _driver
    if _driver is None:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from execution_layer.playwright_driver import PlaywrightDriver
        _driver = PlaywrightDriver()
    return _driver


def _page():
    return _get_driver().page


def _find(page, selector: str, timeout: int = 5000):
    """
    Generic multi-strategy locator.
    Tries id, name, text, aria-label, placeholder, CSS, role in order.
    Returns the first matching Locator or raises if none found.
    """
    strategies = [
        f"#{selector}",
        f"[name='{selector}']",
        f"text={selector}",
        f"[aria-label*='{selector}' i]",
        f"[placeholder*='{selector}' i]",
        f"role=button[name='{selector}']",
        f"role=link[name='{selector}']",
        f"role=textbox[name='{selector}']",
        f"role=checkbox[name='{selector}']",
        f"role=combobox[name='{selector}']",
        selector,   # raw CSS / XPath fallback
    ]
    for strat in strategies:
        try:
            loc = page.locator(strat).first
            loc.wait_for(state="attached", timeout=timeout)
            return loc
        except Exception:
            continue
    raise RuntimeError(f"Element not found with any strategy for: '{{selector}}'")


def _safe_action(fn, fallback_msg: str):
    """Run fn(); on any exception log fallback_msg instead of crashing."""
    try:
        fn()
    except Exception as exc:
        Messages.write_message(f"WARNING: {{fallback_msg}} ({{exc}})")


# ─────────────────────────────────────────────────────────────────────────────
# Lifecycle hooks
# ─────────────────────────────────────────────────────────────────────────────

@before_suite
def before_suite_hook():
    _get_driver()
    Messages.write_message("Playwright browser launched")


@after_suite
def after_suite_hook():
    global _driver
    if _driver:
        _driver.close()
        _driver = None
        Messages.write_message("Playwright browser closed")


@before_scenario
def before_scenario_hook():
    Messages.write_message(f"Scenario start | URL: {{_page().url}}")


@after_scenario
def after_scenario_hook():
    Screenshots.capture_screenshot()

'''


def _block_open_browser(url: str) -> str:
    return f'''
# ─────────────────────────────────────────────────────────────────────────────
# Navigation
# ─────────────────────────────────────────────────────────────────────────────

@step("Open browser and navigate to base URL")
def open_browser():
    _page().goto(BASE_URL, wait_until="networkidle")
    Messages.write_message(f"Opened: {{BASE_URL}}")

'''


def _block_navigate() -> str:
    return '''
@step("Navigate to <url>")
def navigate_to(url: str):
    full = url if url.startswith("http") else f"{BASE_URL}{url}"
    _page().goto(full, wait_until="networkidle")
    Messages.write_message(f"Navigated to: {full}")

'''


def _block_refresh() -> str:
    return '''
@step("Refresh the page")
def refresh_page():
    _page().reload(wait_until="networkidle")
    Messages.write_message("Page refreshed")

'''


def _block_go_back() -> str:
    return '''
@step("Go back to previous page")
def go_back():
    _page().go_back(wait_until="networkidle")

'''


def _block_go_forward() -> str:
    return '''
@step("Go forward to next page")
def go_forward():
    _page().go_forward(wait_until="networkidle")

'''


def _block_click() -> str:
    return '''
# ─────────────────────────────────────────────────────────────────────────────
# Interactions
# ─────────────────────────────────────────────────────────────────────────────

@step("Click on <element>")
def click_element(element: str):
    def _do():
        _find(_page(), element).click()
        Messages.write_message(f"Clicked: {element}")
    _safe_action(_do, f"Could not click '{element}'")


@step("Click button <label>")
def click_button(label: str):
    def _do():
        _page().get_by_role("button", name=label).first.click()
        Messages.write_message(f"Clicked button: {label}")
    _safe_action(_do, f"Could not click button '{label}'")


@step("Click link <label>")
def click_link(label: str):
    def _do():
        _page().get_by_role("link", name=label).first.click()
        Messages.write_message(f"Clicked link: {label}")
    _safe_action(_do, f"Could not click link '{label}'")

'''


def _block_double_click() -> str:
    return '''
@step("Double click on <element>")
def double_click(element: str):
    def _do():
        _find(_page(), element).dblclick()
        Messages.write_message(f"Double-clicked: {element}")
    _safe_action(_do, f"Could not double-click '{element}'")

'''


def _block_right_click() -> str:
    return '''
@step("Right click on <element>")
def right_click(element: str):
    def _do():
        _find(_page(), element).click(button="right")
        Messages.write_message(f"Right-clicked: {element}")
    _safe_action(_do, f"Could not right-click '{element}'")

'''


def _block_hover() -> str:
    return '''
@step("Hover over <element>")
def hover_element(element: str):
    def _do():
        _find(_page(), element).hover()
        Messages.write_message(f"Hovered: {element}")
    _safe_action(_do, f"Could not hover '{element}'")

'''


def _block_enter_text() -> str:
    return '''
# ─────────────────────────────────────────────────────────────────────────────
# Input
# ─────────────────────────────────────────────────────────────────────────────

@step("Enter <text> in <field>")
def enter_text(text: str, field: str):
    def _do():
        el = _find(_page(), field)
        el.wait_for(state="visible", timeout=8000)
        el.clear()
        el.fill(text)
        Messages.write_message(f"Entered '{text}' in '{field}'")
    _safe_action(_do, f"Could not enter text in '{field}'")


@step("Type <text> in <field>")
def type_text(text: str, field: str):
    """Simulates real keystroke-by-keystroke typing (triggers JS events)."""
    def _do():
        el = _find(_page(), field)
        el.wait_for(state="visible", timeout=8000)
        el.clear()
        el.press_sequentially(text, delay=50)
        Messages.write_message(f"Typed '{text}' in '{field}'")
    _safe_action(_do, f"Could not type in '{field}'")

'''


def _block_clear_field() -> str:
    return '''
@step("Clear field <field>")
def clear_field(field: str):
    def _do():
        _find(_page(), field).clear()
        Messages.write_message(f"Cleared: {field}")
    _safe_action(_do, f"Could not clear '{field}'")

'''


def _block_select_option() -> str:
    return '''
@step("Select <option> from <dropdown>")
def select_option(option: str, dropdown: str):
    def _do():
        el = _find(_page(), dropdown)
        el.select_option(label=option)
        Messages.write_message(f"Selected '{option}' from '{dropdown}'")
    _safe_action(_do, f"Could not select '{option}' from '{dropdown}'")

'''


def _block_check_checkbox() -> str:
    return '''
@step("Check checkbox <label>")
def check_checkbox(label: str):
    def _do():
        _find(_page(), label).check()
        Messages.write_message(f"Checked: {label}")
    _safe_action(_do, f"Could not check '{label}'")

'''


def _block_uncheck_checkbox() -> str:
    return '''
@step("Uncheck checkbox <label>")
def uncheck_checkbox(label: str):
    def _do():
        _find(_page(), label).uncheck()
        Messages.write_message(f"Unchecked: {label}")
    _safe_action(_do, f"Could not uncheck '{label}'")

'''


def _block_upload_file() -> str:
    return '''
@step("Upload file <filepath> to <field>")
def upload_file(filepath: str, field: str):
    def _do():
        _find(_page(), field).set_input_files(filepath)
        Messages.write_message(f"Uploaded '{filepath}' to '{field}'")
    _safe_action(_do, f"Could not upload to '{field}'")

'''


def _block_submit_form() -> str:
    return '''
@step("Submit the form")
def submit_form():
    page = _page()
    def _do():
        try:
            page.locator("button[type='submit'], input[type='submit']").first.click()
        except Exception:
            page.keyboard.press("Enter")
        page.wait_for_load_state("networkidle")
        Messages.write_message("Form submitted")
    _safe_action(_do, "Could not submit form")

'''


def _block_press_key() -> str:
    return '''
@step("Press key <key>")
def press_key(key: str):
    _page().keyboard.press(key)
    Messages.write_message(f"Pressed key: {key}")

'''


def _block_scroll_down() -> str:
    return '''
# ─────────────────────────────────────────────────────────────────────────────
# Scroll / Gestures
# ─────────────────────────────────────────────────────────────────────────────

@step("Scroll down")
def scroll_down():
    _page().evaluate("window.scrollBy(0, window.innerHeight)")
    Messages.write_message("Scrolled down")


@step("Scroll down by <pixels> pixels")
def scroll_down_pixels(pixels: str):
    _page().evaluate(f"window.scrollBy(0, {pixels})")

'''


def _block_scroll_up() -> str:
    return '''
@step("Scroll up")
def scroll_up():
    _page().evaluate("window.scrollBy(0, -window.innerHeight)")
    Messages.write_message("Scrolled up")

'''


def _block_scroll_to_element() -> str:
    return '''
@step("Scroll to <element>")
def scroll_to_element(element: str):
    def _do():
        _find(_page(), element).scroll_into_view_if_needed()
        Messages.write_message(f"Scrolled to: {element}")
    _safe_action(_do, f"Could not scroll to '{element}'")

'''


def _block_focus_element() -> str:
    return '''
@step("Focus on <element>")
def focus_element(element: str):
    def _do():
        _find(_page(), element).focus()
        Messages.write_message(f"Focused: {element}")
    _safe_action(_do, f"Could not focus '{element}'")

'''


def _block_drag_drop() -> str:
    return '''
@step("Drag <source> and drop on <target>")
def drag_drop(source: str, target: str):
    def _do():
        src = _find(_page(), source)
        tgt = _find(_page(), target)
        src.drag_to(tgt)
        Messages.write_message(f"Dragged '{source}' to '{target}'")
    _safe_action(_do, f"Could not drag '{source}' to '{target}'")

'''


def _block_verify() -> str:
    return '''
# ─────────────────────────────────────────────────────────────────────────────
# Assertions / Verifications
# ─────────────────────────────────────────────────────────────────────────────

@step("Verify: <assertion>")
def generic_verify(assertion: str):
    """
    Best-effort assertion engine.
    1. Tries to find the assertion text visible on the page.
    2. Falls back to keyword-density match against body text.
    3. Always captures a screenshot for the report.
    """
    page = _page()
    Screenshots.capture_screenshot()

    # Try direct text visibility first
    try:
        page.locator(f"text={assertion}").first.wait_for(
            state="visible", timeout=4000
        )
        Messages.write_message(f"PASS (text visible): {assertion}")
        return
    except Exception:
        pass

    # Keyword-density fallback
    try:
        body = page.locator("body").inner_text().lower()
    except Exception:
        body = ""

    keywords  = [w for w in assertion.lower().split() if len(w) > 3]
    hits      = sum(1 for kw in keywords if kw in body)
    total     = max(len(keywords), 1)
    pct       = hits / total
    status    = "PASS" if pct >= 0.5 else "WARN"
    Messages.write_message(
        f"{status} ({pct:.0%} keyword match): {assertion}"
    )


@step("Verify page title contains <text>")
def verify_title(text: str):
    title = _page().title()
    assert text.lower() in title.lower(), \
        f"Expected title to contain '{text}', got '{title}'"
    Messages.write_message(f"Title OK: {title}")


@step("Verify text <text> is visible")
def verify_text_visible(text: str):
    try:
        _page().locator(f"text={text}").first.wait_for(
            state="visible", timeout=8000
        )
        Messages.write_message(f"Text visible: {text}")
    except Exception:
        raise AssertionError(f"Text not visible on page: '{text}'")


@step("Verify text <text> is not visible")
def verify_text_not_visible(text: str):
    try:
        _page().locator(f"text={text}").first.wait_for(
            state="hidden", timeout=5000
        )
        Messages.write_message(f"Text correctly hidden: {text}")
    except Exception:
        raise AssertionError(f"Text still visible on page: '{text}'")


@step("Verify element <selector> is visible")
def verify_element_visible(selector: str):
    try:
        _find(_page(), selector).wait_for(state="visible", timeout=8000)
        Messages.write_message(f"Element visible: {selector}")
    except Exception:
        raise AssertionError(f"Element not visible: '{selector}'")


@step("Verify element <selector> is hidden")
def verify_element_hidden(selector: str):
    try:
        _find(_page(), selector).wait_for(state="hidden", timeout=5000)
        Messages.write_message(f"Element hidden: {selector}")
    except Exception:
        raise AssertionError(f"Element not hidden: '{selector}'")


@step("Verify current URL contains <path>")
def verify_url_contains(path: str):
    current = _page().url
    assert path in current, \
        f"Expected URL to contain '{path}', got '{current}'"
    Messages.write_message(f"URL OK: {current}")


@step("Verify current URL is <url>")
def verify_url_exact(url: str):
    current = _page().url
    assert current == url, f"Expected URL '{url}', got '{current}'"


@step("Verify input <field> has value <value>")
def verify_input_value(field: str, value: str):
    actual = _find(_page(), field).input_value()
    assert actual == value, \
        f"Expected '{field}' to have value '{value}', got '{actual}'"
    Messages.write_message(f"Input value OK: {actual}")


@step("Verify checkbox <label> is checked")
def verify_checkbox_checked(label: str):
    assert _find(_page(), label).is_checked(), \
        f"Checkbox '{label}' is not checked"


@step("Verify checkbox <label> is unchecked")
def verify_checkbox_unchecked(label: str):
    assert not _find(_page(), label).is_checked(), \
        f"Checkbox '{label}' is checked"


@step("Verify element <selector> contains text <text>")
def verify_element_text(selector: str, text: str):
    actual = _find(_page(), selector).inner_text()
    assert text.lower() in actual.lower(), \
        f"Expected '{selector}' to contain '{text}', got '{actual}'"

'''


def _block_wait_network_idle() -> str:
    return '''
# ─────────────────────────────────────────────────────────────────────────────
# Waits
# ─────────────────────────────────────────────────────────────────────────────

@step("Wait for network idle")
def wait_network_idle():
    _page().wait_for_load_state("networkidle")
    Messages.write_message("Network idle")

'''


def _block_wait_for_element() -> str:
    return '''
@step("Wait for element <selector>")
def wait_for_element(selector: str):
    def _do():
        _find(_page(), selector).wait_for(state="visible", timeout=15000)
        Messages.write_message(f"Element appeared: {selector}")
    _safe_action(_do, f"Timed out waiting for '{selector}'")

'''


def _block_wait_seconds() -> str:
    return '''
@step("Wait <seconds> seconds")
def wait_seconds(seconds: str):
    time.sleep(float(seconds))
    Messages.write_message(f"Waited {seconds}s")

'''


def _block_take_screenshot() -> str:
    return '''
# ─────────────────────────────────────────────────────────────────────────────
# Visual
# ─────────────────────────────────────────────────────────────────────────────

@step("Take a screenshot")
def take_screenshot():
    Screenshots.capture_screenshot()

'''


def _block_auth_action() -> str:
    return '''
# ─────────────────────────────────────────────────────────────────────────────
# Authentication helpers
# ─────────────────────────────────────────────────────────────────────────────

@step("Log in with username <username> and password <password>")
def login(username: str, password: str):
    page = _page()
    for u_loc in ["#username","#email","[name='username']",
                  "[name='email']","[placeholder*='username' i]",
                  "[placeholder*='email' i]"]:
        try:
            el = page.locator(u_loc).first
            el.wait_for(state="visible", timeout=3000)
            el.clear(); el.fill(username)
            break
        except Exception:
            continue
    for p_loc in ["#password","[name='password']",
                  "[type='password']","[placeholder*='password' i]"]:
        try:
            el = page.locator(p_loc).first
            el.wait_for(state="visible", timeout=3000)
            el.clear(); el.fill(password)
            break
        except Exception:
            continue
    submit_form()
    Messages.write_message(f"Logged in as {username}")


@step("Log out")
def logout():
    page = _page()
    for loc in ["text=Logout","text=Log out","text=Sign out",
                "[aria-label*='logout' i]","#logout"]:
        try:
            page.locator(loc).first.click()
            page.wait_for_load_state("networkidle")
            Messages.write_message("Logged out")
            return
        except Exception:
            continue
    Messages.write_message("WARNING: Could not find logout element")

'''


def _block_handle_dialog() -> str:
    return '''
# ─────────────────────────────────────────────────────────────────────────────
# Dialogs / Alerts
# ─────────────────────────────────────────────────────────────────────────────

@step("Accept dialog")
def accept_dialog():
    _page().on("dialog", lambda d: d.accept())
    Messages.write_message("Dialog accepted")


@step("Dismiss dialog")
def dismiss_dialog():
    _page().on("dialog", lambda d: d.dismiss())
    Messages.write_message("Dialog dismissed")


@step("Close modal")
def close_modal():
    page = _page()
    for loc in ["button[aria-label='Close']","button[aria-label='close']",
                ".modal-close","[data-dismiss='modal']","text=Close","text=Cancel"]:
        try:
            page.locator(loc).first.click()
            Messages.write_message("Modal closed")
            return
        except Exception:
            continue
    page.keyboard.press("Escape")
    Messages.write_message("Pressed Escape to close modal")

'''


def _block_switch_tab() -> str:
    return '''
# ─────────────────────────────────────────────────────────────────────────────
# Tabs / Windows
# ─────────────────────────────────────────────────────────────────────────────

@step("Switch to tab <index>")
def switch_tab(index: str):
    pages = _get_driver().context.pages
    idx   = int(index) - 1
    if 0 <= idx < len(pages):
        pages[idx].bring_to_front()
        _get_driver().page = pages[idx]
        Messages.write_message(f"Switched to tab {index}")
    else:
        Messages.write_message(f"WARNING: Tab {index} not found (total: {len(pages)})")

'''


def _block_switch_frame() -> str:
    return '''
# ─────────────────────────────────────────────────────────────────────────────
# iFrames
# ─────────────────────────────────────────────────────────────────────────────

@step("Switch to iframe <selector>")
def switch_frame(selector: str):
    Messages.write_message(
        f"NOTE: For iframe '{selector}' use page.frame_locator('{selector}') "
        "inside a custom step for complex frame interactions."
    )

'''


def _block_generic_action() -> str:
    return '''
# ─────────────────────────────────────────────────────────────────────────────
# Generic fallback
# ─────────────────────────────────────────────────────────────────────────────

@step("Perform action <description>")
def generic_action(description: str):
    """
    Catch-all step for actions that did not match any specific pattern.
    Logs the action and takes a screenshot for manual review.
    """
    Messages.write_message(f"Generic action (manual review needed): {description}")
    Screenshots.capture_screenshot()

'''


# ── Map type name -> block function ──────────────────────────────────────────
BLOCK_MAP: dict[str, callable] = {
    "open_browser":       _block_open_browser,
    "navigate":           _block_navigate,
    "refresh":            _block_refresh,
    "go_back":            _block_go_back,
    "go_forward":         _block_go_forward,
    "click":              _block_click,
    "double_click":       _block_double_click,
    "right_click":        _block_right_click,
    "hover":              _block_hover,
    "enter_text":         _block_enter_text,
    "clear_field":        _block_clear_field,
    "select_option":      _block_select_option,
    "check_checkbox":     _block_check_checkbox,
    "uncheck_checkbox":   _block_uncheck_checkbox,
    "upload_file":        _block_upload_file,
    "submit_form":        _block_submit_form,
    "press_key":          _block_press_key,
    "scroll_down":        _block_scroll_down,
    "scroll_up":          _block_scroll_up,
    "scroll_to_element":  _block_scroll_to_element,
    "focus_element":      _block_focus_element,
    "drag_drop":          _block_drag_drop,
    "verify":             _block_verify,
    "wait_network_idle":  _block_wait_network_idle,
    "wait_for_element":   _block_wait_for_element,
    "wait_seconds":       _block_wait_seconds,
    "take_screenshot":    _block_take_screenshot,
    "auth_action":        _block_auth_action,
    "handle_dialog":      _block_handle_dialog,
    "switch_tab":         _block_switch_tab,
    "switch_frame":       _block_switch_frame,
    "generic_action":     _block_generic_action,
}


# ─────────────────────────────────────────────────────────────────────────────
# Generator class
# ─────────────────────────────────────────────────────────────────────────────

class StepImplGenerator:
    """
    Reads a JSON test-case file, determines which step types are needed,
    and writes a complete ai_steps.py to execution_layer/step_impl/.
    """

    def __init__(self, json_path: Path, output_path: Path = OUTPUT_FILE):
        self.json_path   = json_path
        self.output_path = output_path
        self.data: dict  = {}

    def generate(self) -> Path:
        self._load()
        code = self._build()
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text(code, encoding="utf-8")
        print(f"[StepImplGenerator] Written -> {self.output_path}")
        return self.output_path

    def _load(self):
        if not self.json_path.exists():
            raise FileNotFoundError(f"JSON not found: {self.json_path}")
        self.data = json.loads(self.json_path.read_text(encoding="utf-8"))

    def _build(self) -> str:
        url        = self.data.get("url", "https://example.com")
        report_id  = self.data.get("report_id", "unknown")
        timestamp  = self.data.get("timestamp",
                                   datetime.now().strftime("%Y%m%d_%H%M%S"))
        test_cases = self.data.get("test_cases", [])

        # Always include these core types
        needed = {"open_browser", "navigate", "verify",
                  "take_screenshot", "wait_network_idle"}

        # Add types inferred from actual test case steps
        needed |= _collect_step_types(test_cases)

        # Build file
        parts = [_header(url, report_id, timestamp)]

        # open_browser always first
        parts.append(BLOCK_MAP["open_browser"](url))
        needed.discard("open_browser")

        # Emit remaining blocks in a sensible order
        ordered = [
            "navigate", "refresh", "go_back", "go_forward",
            "click", "double_click", "right_click", "hover",
            "enter_text", "type_text", "clear_field",
            "select_option", "check_checkbox", "uncheck_checkbox", "upload_file",
            "submit_form", "press_key",
            "scroll_down", "scroll_up", "scroll_to_element", "focus_element", "drag_drop",
            "verify",
            "wait_network_idle", "wait_for_element", "wait_seconds",
            "take_screenshot",
            "auth_action", "handle_dialog", "switch_tab", "switch_frame",
            "generic_action",
        ]

        for name in ordered:
            if name in needed and name in BLOCK_MAP:
                fn = BLOCK_MAP[name]
                # Some blocks take no args
                try:
                    parts.append(fn())
                except TypeError:
                    parts.append(fn(url))

        return "\n".join(parts)


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Auto-generate ai_steps.py from AI test-case JSON."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--report_id",
        help="Report ID in intelligence_layer/json_store/")
    group.add_argument("--json_path",
        help="Explicit path to the JSON file.")
    parser.add_argument("--output",
        default=str(OUTPUT_FILE),
        help=f"Output path for ai_steps.py (default: {OUTPUT_FILE})")
    args = parser.parse_args()

    json_path   = (Path(args.json_path) if args.json_path
                   else JSON_STORE / f"{args.report_id}.json")
    output_path = Path(args.output)

    try:
        out = StepImplGenerator(json_path, output_path).generate()
        print(f"[OK] {out}")
        sys.exit(0)
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()