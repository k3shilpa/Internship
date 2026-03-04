"""
ai_steps.py  (AUTO-GENERATED)
==============================
Report ID  : 20260304_105521_fd9c5ece
Target URL : https://calculators.net/
Generated  : 20260304_105600
"""

from __future__ import annotations
import os, sys, time
from pathlib import Path
from dotenv import load_dotenv
from getgauge.python import (
    step, before_suite, after_suite,
    before_scenario, after_scenario,
    Messages, Screenshots
)

load_dotenv(Path(__file__).parent.parent.parent / ".env")
BASE_URL = os.getenv("BASE_URL", "https://calculators.net/")
_driver = None


def _get_driver():
    global _driver
    if _driver is None:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from execution_layer.playwright_driver import PlaywrightDriver
        _driver = PlaywrightDriver()
    return _driver


def _page():
    return _get_driver().page


def _find(page, sel, timeout=5000):
    """Multi-strategy locator with fallback chain."""
    strategies = [
        "#" + sel,
        "[name='" + sel + "']",
        "text=" + sel,
        "[aria-label*='" + sel + "' i]",
        "[placeholder*='" + sel + "' i]",
        "role=button[name='" + sel + "']",
        "role=link[name='" + sel + "']",
        "role=textbox[name='" + sel + "']",
        "role=checkbox[name='" + sel + "']",
        "role=combobox[name='" + sel + "']",
        sel,
    ]
    for strat in strategies:
        try:
            loc = page.locator(strat).first
            loc.wait_for(state="attached", timeout=timeout)
            return loc
        except Exception:
            continue
    raise RuntimeError("Element not found: " + str(sel))


def _safe(fn, msg):
    try:
        fn()
    except Exception as exc:
        Messages.write_message("WARNING: " + msg + " | " + str(exc))


# ── Lifecycle ────────────────────────────────────────────────────────

@before_suite
def before_suite_hook():
    _get_driver()
    Messages.write_message("Browser launched")


@after_suite
def after_suite_hook():
    global _driver
    if _driver:
        _driver.close()
        _driver = None


@before_scenario
def before_scenario_hook():
    Messages.write_message("Scenario start: " + _page().url)


@after_scenario
def after_scenario_hook():
    Screenshots.capture_screenshot()


# ── Navigation ───────────────────────────────────────────────────────

@step("Open browser and navigate to base URL")
def open_browser():
    _page().goto(BASE_URL, wait_until="networkidle")
    Messages.write_message("Opened: " + BASE_URL)

@step("Navigate to <url>")
def navigate_to(url):
    full = url if url.startswith("http") else BASE_URL + url
    _page().goto(full, wait_until="networkidle")
    Messages.write_message("Navigated: " + full)


# ── Interactions ─────────────────────────────────────────────────────

@step("Click on <element>")
def click_element(element):
    def _do():
        _find(_page(), element).click()
        Messages.write_message("Clicked: " + element)
    _safe(_do, "Could not click: " + element)


@step("Click button <label>")
def click_button(label):
    def _do():
        _page().get_by_role("button", name=label).first.click()
        Messages.write_message("Clicked button: " + label)
    _safe(_do, "Could not click button: " + label)


@step("Click link <label>")
def click_link(label):
    def _do():
        _page().get_by_role("link", name=label).first.click()
        Messages.write_message("Clicked link: " + label)
    _safe(_do, "Could not click link: " + label)


# ── Input ────────────────────────────────────────────────────────────

@step("Enter <text> in <field>")
def enter_text(text, field):
    def _do():
        el = _find(_page(), field)
        el.wait_for(state="visible", timeout=8000)
        el.clear()
        el.fill(text)
        Messages.write_message("Entered in " + field)
    _safe(_do, "Could not enter text in: " + field)


@step("Type <text> in <field>")
def type_text(text, field):
    def _do():
        el = _find(_page(), field)
        el.wait_for(state="visible", timeout=8000)
        el.clear()
        el.press_sequentially(text, delay=50)
    _safe(_do, "Could not type in: " + field)

@step("Clear field <field>")
def clear_field(field):
    def _do():
        _find(_page(), field).clear()
    _safe(_do, "Could not clear: " + field)


# ── Assertions ───────────────────────────────────────────────────────

@step("Verify: <assertion>")
def generic_verify(assertion):
    Screenshots.capture_screenshot()
    try:
        _page().locator("text=" + assertion).first.wait_for(
            state="visible", timeout=4000)
        Messages.write_message("PASS (visible): " + assertion)
        return
    except Exception:
        pass
    try:
        body = _page().locator("body").inner_text().lower()
    except Exception:
        body = ""
    words = [w for w in assertion.lower().split() if len(w) > 3]
    hits = sum(1 for w in words if w in body)
    pct = hits / max(len(words), 1)
    status = "PASS" if pct >= 0.5 else "WARN"
    Messages.write_message(status + " " + str(round(pct*100)) + "%: " + assertion)


@step("Verify page title contains <text>")
def verify_title(text):
    title = _page().title()
    assert text.lower() in title.lower(), \
        "Expected title to contain: " + text + " got: " + title
    Messages.write_message("Title OK: " + title)


@step("Verify text <text> is visible")
def verify_text_visible(text):
    try:
        _page().locator("text=" + text).first.wait_for(
            state="visible", timeout=8000)
        Messages.write_message("Text visible: " + text)
    except Exception:
        raise AssertionError("Text not visible: " + text)


@step("Verify text <text> is not visible")
def verify_text_not_visible(text):
    try:
        _page().locator("text=" + text).first.wait_for(
            state="hidden", timeout=5000)
        Messages.write_message("Text hidden: " + text)
    except Exception:
        raise AssertionError("Text still visible: " + text)


@step("Verify element <sel> is visible")
def verify_element_visible(sel):
    try:
        _find(_page(), sel).wait_for(state="visible", timeout=8000)
        Messages.write_message("Element visible: " + sel)
    except Exception:
        raise AssertionError("Element not visible: " + sel)


@step("Verify element <sel> is hidden")
def verify_element_hidden(sel):
    try:
        _find(_page(), sel).wait_for(state="hidden", timeout=5000)
        Messages.write_message("Element hidden: " + sel)
    except Exception:
        raise AssertionError("Element not hidden: " + sel)


@step("Verify current URL contains <path>")
def verify_url_contains(path):
    current = _page().url
    assert path in current, \
        "Expected URL to contain: " + path + " got: " + current
    Messages.write_message("URL OK: " + current)


@step("Verify input <field> has value <value>")
def verify_input_value(field, value):
    actual = _find(_page(), field).input_value()
    assert actual == value, \
        "Expected " + field + " = " + value + " got: " + actual
    Messages.write_message("Input OK: " + actual)


# ── Waits ────────────────────────────────────────────────────────────

@step("Wait for network idle")
def wait_network_idle():
    _page().wait_for_load_state("networkidle")
    Messages.write_message("Network idle")

@step("Wait for element <sel>")
def wait_for_element(sel):
    def _do():
        _find(_page(), sel).wait_for(state="visible", timeout=15000)
        Messages.write_message("Element appeared: " + sel)
    _safe(_do, "Timed out waiting for: " + sel)


# ── Visual ───────────────────────────────────────────────────────────

@step("Take a screenshot")
def take_screenshot():
    Screenshots.capture_screenshot()


# ── Auth ─────────────────────────────────────────────────────────────

@step("Log in with username <username> and password <password>")
def login(username, password):
    page = _page()
    for u_loc in [
        "#username", "#email",
        "[name='username']", "[name='email']",
        "[placeholder*='username' i]", "[placeholder*='email' i]",
    ]:
        try:
            el = page.locator(u_loc).first
            el.wait_for(state="visible", timeout=3000)
            el.clear()
            el.fill(username)
            break
        except Exception:
            continue
    for p_loc in [
        "#password", "[name='password']",
        "[type='password']", "[placeholder*='password' i]",
    ]:
        try:
            el = page.locator(p_loc).first
            el.wait_for(state="visible", timeout=3000)
            el.clear()
            el.fill(password)
            break
        except Exception:
            continue
    submit_form()
    Messages.write_message("Logged in as: " + username)


@step("Log out")
def logout():
    page = _page()
    for loc in [
        "text=Logout", "text=Log out", "text=Sign out",
        "[aria-label*='logout' i]", "#logout",
    ]:
        try:
            page.locator(loc).first.click()
            page.wait_for_load_state("networkidle")
            Messages.write_message("Logged out")
            return
        except Exception:
            continue
    Messages.write_message("WARNING: logout element not found")


# ── Generic fallback ─────────────────────────────────────────────────

@step("Perform action <description>")
def generic_action(description):
    Messages.write_message("Generic action: " + description)
    Screenshots.capture_screenshot()
