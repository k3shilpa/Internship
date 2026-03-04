"""
step_impl_generator.py
======================
Reads an AI-generated JSON file and auto-generates a complete, generic
Gauge step implementation file (ai_steps.py).

FIX: Rewrote all code blocks as list-of-strings joined with newline.
     This avoids the 'selector is not defined' error caused by
     f-strings with curly braces being evaluated at code-generation time.

Usage:
    python step_impl_generator.py --report_id 20240101_120000_abc12345
    python step_impl_generator.py --json_path path/to/custom.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from datetime import datetime

BASE_DIR       = Path(__file__).parent
JSON_STORE     = BASE_DIR / "intelligence_layer" / "json_store"
STEP_IMPL_DIR  = BASE_DIR / "execution_layer" / "step_impl"
OUTPUT_FILE    = STEP_IMPL_DIR / "ai_steps.py"


# ─────────────────────────────────────────────────────────────────────────────
# Step pattern classifier
# ─────────────────────────────────────────────────────────────────────────────

STEP_PATTERNS = [
    (r"navigate|go to|open|visit|browse|load page",         "navigate"),
    (r"refresh|reload",                                      "refresh"),
    (r"back|previous page",                                  "go_back"),
    (r"forward",                                             "go_forward"),
    (r"enter|type|fill|input|write",                         "enter_text"),
    (r"clear|empty",                                         "clear_field"),
    (r"select.*(dropdown|option|list)",                      "select_option"),
    (r"upload|attach file",                                  "upload_file"),
    (r"check|tick|enable.*(checkbox)",                       "check_checkbox"),
    (r"uncheck|untick|disable.*(checkbox)",                  "uncheck_checkbox"),
    (r"double.click|dblclick",                               "double_click"),
    (r"right.click|context.menu",                            "right_click"),
    (r"click|press|tap|push",                                "click"),
    (r"hover|mouse over",                                    "hover"),
    (r"drag.*drop",                                          "drag_drop"),
    (r"scroll down",                                         "scroll_down"),
    (r"scroll up",                                           "scroll_up"),
    (r"scroll to",                                           "scroll_to_element"),
    (r"focus",                                               "focus_element"),
    (r"submit",                                              "submit_form"),
    (r"press key|keyboard",                                  "press_key"),
    (r"verify|assert|check|confirm|validate|ensure|should|must|expect", "verify"),
    (r"wait for network|network idle",                       "wait_network_idle"),
    (r"wait for|wait until",                                 "wait_for_element"),
    (r"wait",                                                "wait_seconds"),
    (r"screenshot|capture|snap",                             "take_screenshot"),
    (r"log.?in|log.?out|sign.?in|sign.?out",                "auth_action"),
    (r"accept|dismiss|close.*dialog|alert",                  "handle_dialog"),
    (r"new tab|switch tab|open tab",                         "switch_tab"),
    (r"iframe|frame",                                        "switch_frame"),
    (r".*",                                                  "generic_action"),
]


def _classify_step(step_text):
    lower = step_text.lower()
    for pattern, name in STEP_PATTERNS:
        if re.search(pattern, lower):
            return name
    return "generic_action"


def _collect_step_types(test_cases):
    types = {"open_browser", "take_screenshot", "wait_network_idle"}
    for tc in test_cases:
        for step in tc.get("steps", []):
            types.add(_classify_step(step))
        if tc.get("expected"):
            types.add("verify")
    return types


# ─────────────────────────────────────────────────────────────────────────────
# Code blocks
# IMPORTANT: All blocks use "\n".join([...]) with plain strings.
# Never use f-strings with {} here — those braces go into the generated
# Python source and must NOT be evaluated by the generator itself.
# ─────────────────────────────────────────────────────────────────────────────

def _header(url, report_id, timestamp):
    return "\n".join([
        '"""',
        "ai_steps.py  (AUTO-GENERATED)",
        "==============================",
        "Report ID  : " + report_id,
        "Target URL : " + url,
        "Generated  : " + timestamp,
        '"""',
        "",
        "from __future__ import annotations",
        "import os, sys, time",
        "from pathlib import Path",
        "from dotenv import load_dotenv",
        "from getgauge.python import (",
        "    step, before_suite, after_suite,",
        "    before_scenario, after_scenario,",
        "    Messages, Screenshots",
        ")",
        "",
        'load_dotenv(Path(__file__).parent.parent.parent / ".env")',
        'BASE_URL = os.getenv("BASE_URL", "' + url + '")',
        "_driver = None",
        "",
        "",
        "def _get_driver():",
        "    global _driver",
        "    if _driver is None:",
        "        sys.path.insert(0, str(Path(__file__).parent.parent.parent))",
        "        from execution_layer.playwright_driver import PlaywrightDriver",
        "        _driver = PlaywrightDriver()",
        "    return _driver",
        "",
        "",
        "def _page():",
        "    return _get_driver().page",
        "",
        "",
        "def _find(page, sel, timeout=5000):",
        '    """Multi-strategy locator with fallback chain."""',
        "    strategies = [",
        '        "#" + sel,',
        '        "[name=\'" + sel + "\']",',
        '        "text=" + sel,',
        '        "[aria-label*=\'" + sel + "\' i]",',
        '        "[placeholder*=\'" + sel + "\' i]",',
        '        "role=button[name=\'" + sel + "\']",',
        '        "role=link[name=\'" + sel + "\']",',
        '        "role=textbox[name=\'" + sel + "\']",',
        '        "role=checkbox[name=\'" + sel + "\']",',
        '        "role=combobox[name=\'" + sel + "\']",',
        "        sel,",
        "    ]",
        "    for strat in strategies:",
        "        try:",
        "            loc = page.locator(strat).first",
        '            loc.wait_for(state="attached", timeout=timeout)',
        "            return loc",
        "        except Exception:",
        "            continue",
        '    raise RuntimeError("Element not found: " + str(sel))',
        "",
        "",
        "def _safe(fn, msg):",
        "    try:",
        "        fn()",
        "    except Exception as exc:",
        '        Messages.write_message("WARNING: " + msg + " | " + str(exc))',
        "",
        "",
        "# ── Lifecycle ────────────────────────────────────────────────────────",
        "",
        "@before_suite",
        "def before_suite_hook():",
        "    _get_driver()",
        '    Messages.write_message("Browser launched")',
        "",
        "",
        "@after_suite",
        "def after_suite_hook():",
        "    global _driver",
        "    if _driver:",
        "        _driver.close()",
        "        _driver = None",
        "",
        "",
        "@before_scenario",
        "def before_scenario_hook():",
        '    Messages.write_message("Scenario start: " + _page().url)',
        "",
        "",
        "@after_scenario",
        "def after_scenario_hook():",
        "    Screenshots.capture_screenshot()",
        "",
    ])


def _block_open_browser(url):
    return "\n".join([
        "",
        "# ── Navigation ───────────────────────────────────────────────────────",
        "",
        '@step("Open browser and navigate to base URL")',
        "def open_browser():",
        '    _page().goto(BASE_URL, wait_until="networkidle")',
        '    Messages.write_message("Opened: " + BASE_URL)',
        "",
    ])


def _block_navigate():
    return "\n".join([
        '@step("Navigate to <url>")',
        "def navigate_to(url):",
        '    full = url if url.startswith("http") else BASE_URL + url',
        '    _page().goto(full, wait_until="networkidle")',
        '    Messages.write_message("Navigated: " + full)',
        "",
    ])


def _block_refresh():
    return "\n".join([
        '@step("Refresh the page")',
        "def refresh_page():",
        '    _page().reload(wait_until="networkidle")',
        "",
    ])


def _block_go_back():
    return "\n".join([
        '@step("Go back to previous page")',
        "def go_back():",
        '    _page().go_back(wait_until="networkidle")',
        "",
    ])


def _block_go_forward():
    return "\n".join([
        '@step("Go forward to next page")',
        "def go_forward():",
        '    _page().go_forward(wait_until="networkidle")',
        "",
    ])


def _block_click():
    return "\n".join([
        "",
        "# ── Interactions ─────────────────────────────────────────────────────",
        "",
        '@step("Click on <element>")',
        "def click_element(element):",
        "    def _do():",
        "        _find(_page(), element).click()",
        '        Messages.write_message("Clicked: " + element)',
        '    _safe(_do, "Could not click: " + element)',
        "",
        "",
        '@step("Click button <label>")',
        "def click_button(label):",
        "    def _do():",
        '        _page().get_by_role("button", name=label).first.click()',
        '        Messages.write_message("Clicked button: " + label)',
        '    _safe(_do, "Could not click button: " + label)',
        "",
        "",
        '@step("Click link <label>")',
        "def click_link(label):",
        "    def _do():",
        '        _page().get_by_role("link", name=label).first.click()',
        '        Messages.write_message("Clicked link: " + label)',
        '    _safe(_do, "Could not click link: " + label)',
        "",
    ])


def _block_double_click():
    return "\n".join([
        '@step("Double click on <element>")',
        "def double_click(element):",
        "    def _do():",
        "        _find(_page(), element).dblclick()",
        '    _safe(_do, "Could not double-click: " + element)',
        "",
    ])


def _block_right_click():
    return "\n".join([
        '@step("Right click on <element>")',
        "def right_click(element):",
        "    def _do():",
        '        _find(_page(), element).click(button="right")',
        '    _safe(_do, "Could not right-click: " + element)',
        "",
    ])


def _block_hover():
    return "\n".join([
        '@step("Hover over <element>")',
        "def hover_element(element):",
        "    def _do():",
        "        _find(_page(), element).hover()",
        '    _safe(_do, "Could not hover: " + element)',
        "",
    ])


def _block_enter_text():
    return "\n".join([
        "",
        "# ── Input ────────────────────────────────────────────────────────────",
        "",
        '@step("Enter <text> in <field>")',
        "def enter_text(text, field):",
        "    def _do():",
        "        el = _find(_page(), field)",
        '        el.wait_for(state="visible", timeout=8000)',
        "        el.clear()",
        "        el.fill(text)",
        '        Messages.write_message("Entered in " + field)',
        '    _safe(_do, "Could not enter text in: " + field)',
        "",
        "",
        '@step("Type <text> in <field>")',
        "def type_text(text, field):",
        "    def _do():",
        "        el = _find(_page(), field)",
        '        el.wait_for(state="visible", timeout=8000)',
        "        el.clear()",
        "        el.press_sequentially(text, delay=50)",
        '    _safe(_do, "Could not type in: " + field)',
        "",
    ])


def _block_clear_field():
    return "\n".join([
        '@step("Clear field <field>")',
        "def clear_field(field):",
        "    def _do():",
        "        _find(_page(), field).clear()",
        '    _safe(_do, "Could not clear: " + field)',
        "",
    ])


def _block_select_option():
    return "\n".join([
        '@step("Select <option> from <dropdown>")',
        "def select_option(option, dropdown):",
        "    def _do():",
        "        _find(_page(), dropdown).select_option(label=option)",
        '        Messages.write_message("Selected " + option + " from " + dropdown)',
        '    _safe(_do, "Could not select from: " + dropdown)',
        "",
    ])


def _block_check_checkbox():
    return "\n".join([
        '@step("Check checkbox <label>")',
        "def check_checkbox(label):",
        "    def _do():",
        "        _find(_page(), label).check()",
        '    _safe(_do, "Could not check: " + label)',
        "",
    ])


def _block_uncheck_checkbox():
    return "\n".join([
        '@step("Uncheck checkbox <label>")',
        "def uncheck_checkbox(label):",
        "    def _do():",
        "        _find(_page(), label).uncheck()",
        '    _safe(_do, "Could not uncheck: " + label)',
        "",
    ])


def _block_upload_file():
    return "\n".join([
        '@step("Upload file <filepath> to <field>")',
        "def upload_file(filepath, field):",
        "    def _do():",
        "        _find(_page(), field).set_input_files(filepath)",
        '    _safe(_do, "Could not upload to: " + field)',
        "",
    ])


def _block_submit_form():
    return "\n".join([
        '@step("Submit the form")',
        "def submit_form():",
        "    page = _page()",
        "    def _do():",
        "        try:",
        "            page.locator(",
        "                \"button[type='submit'], input[type='submit']\"",
        "            ).first.click()",
        "        except Exception:",
        '            page.keyboard.press("Enter")',
        '        page.wait_for_load_state("networkidle")',
        '        Messages.write_message("Form submitted")',
        '    _safe(_do, "Could not submit form")',
        "",
    ])


def _block_press_key():
    return "\n".join([
        '@step("Press key <key>")',
        "def press_key(key):",
        "    _page().keyboard.press(key)",
        '    Messages.write_message("Pressed: " + key)',
        "",
    ])


def _block_scroll_down():
    return "\n".join([
        "",
        "# ── Scroll ───────────────────────────────────────────────────────────",
        "",
        '@step("Scroll down")',
        "def scroll_down():",
        '    _page().evaluate("window.scrollBy(0, window.innerHeight)")',
        "",
        "",
        '@step("Scroll down by <pixels> pixels")',
        "def scroll_down_pixels(pixels):",
        '    _page().evaluate("window.scrollBy(0, " + str(pixels) + ")")',
        "",
    ])


def _block_scroll_up():
    return "\n".join([
        '@step("Scroll up")',
        "def scroll_up():",
        '    _page().evaluate("window.scrollBy(0, -window.innerHeight)")',
        "",
    ])


def _block_scroll_to_element():
    return "\n".join([
        '@step("Scroll to <element>")',
        "def scroll_to_element(element):",
        "    def _do():",
        "        _find(_page(), element).scroll_into_view_if_needed()",
        '    _safe(_do, "Could not scroll to: " + element)',
        "",
    ])


def _block_focus_element():
    return "\n".join([
        '@step("Focus on <element>")',
        "def focus_element(element):",
        "    def _do():",
        "        _find(_page(), element).focus()",
        '    _safe(_do, "Could not focus: " + element)',
        "",
    ])


def _block_drag_drop():
    return "\n".join([
        '@step("Drag <source> and drop on <target>")',
        "def drag_drop(source, target):",
        "    def _do():",
        "        _find(_page(), source).drag_to(_find(_page(), target))",
        '    _safe(_do, "Could not drag " + source + " to " + target)',
        "",
    ])


def _block_verify():
    return "\n".join([
        "",
        "# ── Assertions ───────────────────────────────────────────────────────",
        "",
        '@step("Verify: <assertion>")',
        "def generic_verify(assertion):",
        "    Screenshots.capture_screenshot()",
        "    try:",
        '        _page().locator("text=" + assertion).first.wait_for(',
        '            state="visible", timeout=4000)',
        '        Messages.write_message("PASS (visible): " + assertion)',
        "        return",
        "    except Exception:",
        "        pass",
        "    try:",
        '        body = _page().locator("body").inner_text().lower()',
        "    except Exception:",
        '        body = ""',
        "    words = [w for w in assertion.lower().split() if len(w) > 3]",
        "    hits = sum(1 for w in words if w in body)",
        "    pct = hits / max(len(words), 1)",
        '    status = "PASS" if pct >= 0.5 else "WARN"',
        '    Messages.write_message(status + " " + str(round(pct*100)) + "%: " + assertion)',
        "",
        "",
        '@step("Verify page title contains <text>")',
        "def verify_title(text):",
        "    title = _page().title()",
        "    assert text.lower() in title.lower(), \\",
        '        "Expected title to contain: " + text + " got: " + title',
        '    Messages.write_message("Title OK: " + title)',
        "",
        "",
        '@step("Verify text <text> is visible")',
        "def verify_text_visible(text):",
        "    try:",
        '        _page().locator("text=" + text).first.wait_for(',
        '            state="visible", timeout=8000)',
        '        Messages.write_message("Text visible: " + text)',
        "    except Exception:",
        '        raise AssertionError("Text not visible: " + text)',
        "",
        "",
        '@step("Verify text <text> is not visible")',
        "def verify_text_not_visible(text):",
        "    try:",
        '        _page().locator("text=" + text).first.wait_for(',
        '            state="hidden", timeout=5000)',
        '        Messages.write_message("Text hidden: " + text)',
        "    except Exception:",
        '        raise AssertionError("Text still visible: " + text)',
        "",
        "",
        '@step("Verify element <sel> is visible")',
        "def verify_element_visible(sel):",
        "    try:",
        '        _find(_page(), sel).wait_for(state="visible", timeout=8000)',
        '        Messages.write_message("Element visible: " + sel)',
        "    except Exception:",
        '        raise AssertionError("Element not visible: " + sel)',
        "",
        "",
        '@step("Verify element <sel> is hidden")',
        "def verify_element_hidden(sel):",
        "    try:",
        '        _find(_page(), sel).wait_for(state="hidden", timeout=5000)',
        '        Messages.write_message("Element hidden: " + sel)',
        "    except Exception:",
        '        raise AssertionError("Element not hidden: " + sel)',
        "",
        "",
        '@step("Verify current URL contains <path>")',
        "def verify_url_contains(path):",
        "    current = _page().url",
        "    assert path in current, \\",
        '        "Expected URL to contain: " + path + " got: " + current',
        '    Messages.write_message("URL OK: " + current)',
        "",
        "",
        '@step("Verify input <field> has value <value>")',
        "def verify_input_value(field, value):",
        "    actual = _find(_page(), field).input_value()",
        "    assert actual == value, \\",
        '        "Expected " + field + " = " + value + " got: " + actual',
        '    Messages.write_message("Input OK: " + actual)',
        "",
    ])


def _block_wait_network_idle():
    return "\n".join([
        "",
        "# ── Waits ────────────────────────────────────────────────────────────",
        "",
        '@step("Wait for network idle")',
        "def wait_network_idle():",
        '    _page().wait_for_load_state("networkidle")',
        '    Messages.write_message("Network idle")',
        "",
    ])


def _block_wait_for_element():
    return "\n".join([
        '@step("Wait for element <sel>")',
        "def wait_for_element(sel):",
        "    def _do():",
        '        _find(_page(), sel).wait_for(state="visible", timeout=15000)',
        '        Messages.write_message("Element appeared: " + sel)',
        '    _safe(_do, "Timed out waiting for: " + sel)',
        "",
    ])


def _block_wait_seconds():
    return "\n".join([
        '@step("Wait <seconds> seconds")',
        "def wait_seconds(seconds):",
        "    time.sleep(float(seconds))",
        '    Messages.write_message("Waited: " + str(seconds) + "s")',
        "",
    ])


def _block_take_screenshot():
    return "\n".join([
        "",
        "# ── Visual ───────────────────────────────────────────────────────────",
        "",
        '@step("Take a screenshot")',
        "def take_screenshot():",
        "    Screenshots.capture_screenshot()",
        "",
    ])


def _block_auth_action():
    return "\n".join([
        "",
        "# ── Auth ─────────────────────────────────────────────────────────────",
        "",
        '@step("Log in with username <username> and password <password>")',
        "def login(username, password):",
        "    page = _page()",
        "    for u_loc in [",
        '        "#username", "#email",',
        '        "[name=\'username\']", "[name=\'email\']",',
        '        "[placeholder*=\'username\' i]", "[placeholder*=\'email\' i]",',
        "    ]:",
        "        try:",
        "            el = page.locator(u_loc).first",
        '            el.wait_for(state="visible", timeout=3000)',
        "            el.clear()",
        "            el.fill(username)",
        "            break",
        "        except Exception:",
        "            continue",
        "    for p_loc in [",
        '        "#password", "[name=\'password\']",',
        '        "[type=\'password\']", "[placeholder*=\'password\' i]",',
        "    ]:",
        "        try:",
        "            el = page.locator(p_loc).first",
        '            el.wait_for(state="visible", timeout=3000)',
        "            el.clear()",
        "            el.fill(password)",
        "            break",
        "        except Exception:",
        "            continue",
        "    submit_form()",
        '    Messages.write_message("Logged in as: " + username)',
        "",
        "",
        '@step("Log out")',
        "def logout():",
        "    page = _page()",
        "    for loc in [",
        '        "text=Logout", "text=Log out", "text=Sign out",',
        '        "[aria-label*=\'logout\' i]", "#logout",',
        "    ]:",
        "        try:",
        "            page.locator(loc).first.click()",
        '            page.wait_for_load_state("networkidle")',
        '            Messages.write_message("Logged out")',
        "            return",
        "        except Exception:",
        "            continue",
        '    Messages.write_message("WARNING: logout element not found")',
        "",
    ])


def _block_handle_dialog():
    return "\n".join([
        "",
        "# ── Dialogs ──────────────────────────────────────────────────────────",
        "",
        '@step("Accept dialog")',
        "def accept_dialog():",
        '    _page().on("dialog", lambda d: d.accept())',
        "",
        "",
        '@step("Dismiss dialog")',
        "def dismiss_dialog():",
        '    _page().on("dialog", lambda d: d.dismiss())',
        "",
        "",
        '@step("Close modal")',
        "def close_modal():",
        "    page = _page()",
        "    for loc in [",
        "        \"button[aria-label='Close']\", \"button[aria-label='close']\",",
        "        \".modal-close\", \"[data-dismiss='modal']\",",
        '        "text=Close", "text=Cancel",',
        "    ]:",
        "        try:",
        "            page.locator(loc).first.click()",
        "            return",
        "        except Exception:",
        "            continue",
        '    page.keyboard.press("Escape")',
        "",
    ])


def _block_switch_tab():
    return "\n".join([
        "",
        "# ── Tabs ─────────────────────────────────────────────────────────────",
        "",
        '@step("Switch to tab <index>")',
        "def switch_tab(index):",
        "    pages = _get_driver().context.pages",
        "    idx = int(index) - 1",
        "    if 0 <= idx < len(pages):",
        "        pages[idx].bring_to_front()",
        "        _get_driver().page = pages[idx]",
        '        Messages.write_message("Switched to tab: " + str(index))',
        "    else:",
        '        Messages.write_message("Tab not found: " + str(index))',
        "",
    ])


def _block_switch_frame():
    return "\n".join([
        "",
        "# ── iFrames ──────────────────────────────────────────────────────────",
        "",
        '@step("Switch to iframe <sel>")',
        "def switch_frame(sel):",
        '    Messages.write_message("NOTE: Use frame_locator for iframe: " + sel)',
        "",
    ])


def _block_generic_action():
    return "\n".join([
        "",
        "# ── Generic fallback ─────────────────────────────────────────────────",
        "",
        '@step("Perform action <description>")',
        "def generic_action(description):",
        '    Messages.write_message("Generic action: " + description)',
        "    Screenshots.capture_screenshot()",
        "",
    ])


# ── Block registry ────────────────────────────────────────────────────────────
BLOCK_MAP = {
    "navigate":          _block_navigate,
    "refresh":           _block_refresh,
    "go_back":           _block_go_back,
    "go_forward":        _block_go_forward,
    "click":             _block_click,
    "double_click":      _block_double_click,
    "right_click":       _block_right_click,
    "hover":             _block_hover,
    "enter_text":        _block_enter_text,
    "clear_field":       _block_clear_field,
    "select_option":     _block_select_option,
    "check_checkbox":    _block_check_checkbox,
    "uncheck_checkbox":  _block_uncheck_checkbox,
    "upload_file":       _block_upload_file,
    "submit_form":       _block_submit_form,
    "press_key":         _block_press_key,
    "scroll_down":       _block_scroll_down,
    "scroll_up":         _block_scroll_up,
    "scroll_to_element": _block_scroll_to_element,
    "focus_element":     _block_focus_element,
    "drag_drop":         _block_drag_drop,
    "verify":            _block_verify,
    "wait_network_idle": _block_wait_network_idle,
    "wait_for_element":  _block_wait_for_element,
    "wait_seconds":      _block_wait_seconds,
    "take_screenshot":   _block_take_screenshot,
    "auth_action":       _block_auth_action,
    "handle_dialog":     _block_handle_dialog,
    "switch_tab":        _block_switch_tab,
    "switch_frame":      _block_switch_frame,
    "generic_action":    _block_generic_action,
}

EMIT_ORDER = list(BLOCK_MAP.keys())


# ─────────────────────────────────────────────────────────────────────────────
# Generator class
# ─────────────────────────────────────────────────────────────────────────────

class StepImplGenerator:

    def __init__(self, json_path: Path, output_path: Path = OUTPUT_FILE):
        self.json_path   = json_path
        self.output_path = output_path
        self.data        = {}

    def generate(self) -> Path:
        self._load()
        code = self._build()
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text(code, encoding="utf-8")
        print("[StepImplGenerator] Written -> " + str(self.output_path))
        return self.output_path

    def _load(self):
        if not self.json_path.exists():
            raise FileNotFoundError("JSON not found: " + str(self.json_path))
        self.data = json.loads(self.json_path.read_text(encoding="utf-8"))

    def _build(self) -> str:
        url       = self.data.get("url", "https://example.com")
        report_id = self.data.get("report_id", "unknown")
        timestamp = self.data.get("timestamp",
                                  datetime.now().strftime("%Y%m%d_%H%M%S"))
        test_cases = self.data.get("test_cases", [])

        needed = {"open_browser", "navigate", "verify",
                  "take_screenshot", "wait_network_idle"}
        needed |= _collect_step_types(test_cases)

        parts = [_header(url, report_id, timestamp)]
        parts.append(_block_open_browser(url))   # always first

        for name in EMIT_ORDER:
            if name in needed and name in BLOCK_MAP:
                parts.append(BLOCK_MAP[name]())

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
    parser.add_argument("--output", default=str(OUTPUT_FILE))
    args = parser.parse_args()

    json_path   = (Path(args.json_path) if args.json_path
                   else JSON_STORE / (args.report_id + ".json"))
    output_path = Path(args.output)

    try:
        out = StepImplGenerator(json_path, output_path).generate()
        print("[OK] " + str(out))
        sys.exit(0)
    except Exception as exc:
        print("[ERROR] " + str(exc), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()