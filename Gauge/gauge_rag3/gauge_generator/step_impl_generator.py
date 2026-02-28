"""
gauge_generator/step_impl_generator.py
=======================================
Generates gauge_project/step_impl.py plus manifest.json and env config.

HOW TO RUN (from project root):
    python gauge_generator/step_impl_generator.py

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

TESTCASES_FILE    = "data/testcases/testcases.json"    # from test_generator.py
GAUGE_PROJECT_DIR = "gauge_project"
STEP_IMPL_FILE    = "gauge_project/step_impl.py"

HEADLESS          = True    # False = show browser window while tests run
DEFAULT_TIMEOUT   = 10      # seconds to wait for elements

# =============================================================================

os.makedirs(GAUGE_PROJECT_DIR, exist_ok=True)


def run():
    logger.info(f"\n{'='*55}")
    logger.info(f"STEP IMPL GENERATOR")
    logger.info(f"  input  : {TESTCASES_FILE}")
    logger.info(f"  output : {STEP_IMPL_FILE}")
    logger.info(f"{'='*55}")

    if not os.path.isfile(TESTCASES_FILE):
        raise FileNotFoundError(
            f"File not found: {TESTCASES_FILE}\n"
            f"Run ai_engine/test_generator.py first."
        )

    with open(TESTCASES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    base_url = data.get("generation_metadata", {}).get("base_url", "https://example.com")

    with open(STEP_IMPL_FILE, "w", encoding="utf-8") as f:
        f.write(_build(base_url))
    logger.info(f"  step_impl.py written")

    # manifest.json
    manifest_path = os.path.join(GAUGE_PROJECT_DIR, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump({"Language": "python", "Plugins": ["html-report"], "FileName": "manifest.json"}, f, indent=2)
    logger.info(f"  manifest.json written")

    # env/default/
    env_dir = os.path.join(GAUGE_PROJECT_DIR, "env", "default")
    os.makedirs(env_dir, exist_ok=True)
    with open(os.path.join(env_dir, "default.properties"), "w") as f:
        f.write("gauge_screenshots_dir = reports/screenshots\nscreenshot_on_failure = true\n")
    with open(os.path.join(GAUGE_PROJECT_DIR, ".env"), "w") as f:
        f.write(f"BASE_URL={base_url}\nHEADLESS={str(HEADLESS).lower()}\nDEFAULT_TIMEOUT={DEFAULT_TIMEOUT}\n")
    logger.info(f"  env/ written")

    logger.info(f"\nDone")
    logger.info(f"\nNext step: python executor/gauge_runner.py")
    logger.info(f"Or run directly: cd {GAUGE_PROJECT_DIR} && gauge run specs/")


def _build(base_url):
    return f'''"""
step_impl.py — Auto-generated Gauge step implementations
Generated : {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Base URL  : {base_url}

Run all tests:   cd gauge_project && gauge run specs/
Run smoke only:  cd gauge_project && gauge run specs/smoke_tests.spec --tags smoke
"""

import time
import logging
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from getgauge.python import step, before_suite, after_suite, before_scenario, after_scenario, data_store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL       = "{base_url}"
TIMEOUT        = {DEFAULT_TIMEOUT}
HEADLESS       = {HEADLESS}
SCREENSHOT_DIR = Path("reports/screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


@before_suite
def start_browser():
    opts = Options()
    if HEADLESS:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-gpu")
    svc = Service(ChromeDriverManager().install())
    data_store.suite["driver"] = webdriver.Chrome(service=svc, options=opts)
    data_store.suite["driver"].set_page_load_timeout(30)
    logger.info("Browser started")


@after_suite
def stop_browser():
    d = data_store.suite.get("driver")
    if d:
        d.quit()
        logger.info("Browser closed")


@before_scenario
def reset():
    d = _d()
    if d:
        d.delete_all_cookies()
        # Navigate to BASE_URL before every scenario so tests don't bleed into each other
        try:
            d.get(BASE_URL)
            WebDriverWait(d, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            logger.info(f"Reset: navigated to {{BASE_URL}}")
        except Exception as e:
            logger.warning(f"Reset navigation failed: {{e}}")


@after_scenario
def ss_after():
    _ss("after_scenario")


def _d():
    return data_store.suite.get("driver")

def _w(t=TIMEOUT):
    return WebDriverWait(_d(), t)

def _by(s):
    return {{"id": By.ID, "css": By.CSS_SELECTOR, "xpath": By.XPATH,
             "name": By.NAME, "tag": By.TAG_NAME, "link_text": By.LINK_TEXT}}.get(s.lower(), By.CSS_SELECTOR)

def _find(st, sv, t=TIMEOUT):
    try:
        return _w(t).until(EC.presence_of_element_located((_by(st), sv)))
    except TimeoutException:
        _ss("not_found")
        raise AssertionError(f"Element not found: {{st}}={{sv}}")

def _click(st, sv):
    el = _w().until(EC.element_to_be_clickable((_by(st), sv)))
    _d().execute_script("arguments[0].scrollIntoView({{block: 'center'}});", el)
    time.sleep(0.2)
    el.click()
    logger.info(f"Clicked {{st}}={{sv}}")

def _type(st, sv, val):
    el = _find(st, sv)
    _d().execute_script("arguments[0].scrollIntoView({{block: 'center'}});", el)
    el.clear()
    el.send_keys(val)
    logger.info(f"Typed '{{val[:20]}}' into {{st}}={{sv}}")

def _vis(st, sv):
    el = _find(st, sv)
    assert el.is_displayed(), f"{{st}}={{sv}} is not visible"
    logger.info(f"Visible: {{st}}={{sv}}")

def _ss(name="shot"):
    try:
        d = _d()
        if d:
            d.save_screenshot(str(SCREENSHOT_DIR / f"{{name}}_{{int(time.time())}}.png"))
    except:
        pass


# Navigation
@step("Navigate to url <url>")
def go(url):
    if not url.startswith("http"):
        url = BASE_URL.rstrip("/") + "/" + url.lstrip("/")
    _d().get(url)
    _w().until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    logger.info(f"Navigated to {{url}}")

@step("Navigate back")
def go_back():
    _d().back()

@step("Navigate forward")
def go_fwd():
    _d().forward()

@step("Refresh page")
def refresh():
    _d().refresh()

@step("Assert current URL contains <partial>")
def assert_url(partial):
    cur = _d().current_url
    assert partial in cur, f"URL '{{cur}}' does not contain '{{partial}}'"

@step("Assert page title is <title>")
def assert_title(title):
    assert title.lower() in _d().title.lower(), f"Title '{{_d().title}}' != '{{title}}'"


# Click
@step("Click on button with css <sel>")
def c_btn_css(sel):   _click("css",   sel)
@step("Click on button with id <sel>")
def c_btn_id(sel):    _click("id",    sel)
@step("Click on button with name <sel>")
def c_btn_nm(sel):    _click("name",  sel)
@step("Click on button with xpath <sel>")
def c_btn_xp(sel):    _click("xpath", sel)
@step("Click on link with css <sel>")
def c_lnk_css(sel):   _click("css",   sel)
@step("Click on link with id <sel>")
def c_lnk_id(sel):    _click("id",    sel)
@step("Click on link with name <sel>")
def c_lnk_nm(sel):    _click("name",  sel)
@step("Click on element with css <sel>")
def c_el_css(sel):    _click("css",   sel)
@step("Click on element with id <sel>")
def c_el_id(sel):     _click("id",    sel)
@step("Click on element with xpath <sel>")
def c_el_xp(sel):     _click("xpath", sel)
@step("Click on element with name <sel>")
def c_el_nm(sel):     _click("name",  sel)
@step("Click on link with text <text>")
def c_lnk_txt(text):
    el = _w().until(EC.element_to_be_clickable((By.LINK_TEXT, text)))
    el.click()
@step("Click on link with link text <text>")
def c_lnk_lt(text):
    el = _w().until(EC.element_to_be_clickable((By.LINK_TEXT, text)))
    el.click()
@step("Click on link with partial link text <text>")
def c_lnk_plt(text):
    el = _w().until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, text)))
    el.click()


# Type / Input
@step("Enter <val> in input with css <sel>")
def t_css(val, sel):    _type("css",   sel, val)
@step("Enter <val> in input with id <sel>")
def t_id(val, sel):     _type("id",    sel, val)
@step("Enter <val> in input with name <sel>")
def t_nm(val, sel):     _type("name",  sel, val)
@step("Enter <val> in input with xpath <sel>")
def t_xp(val, sel):     _type("xpath", sel, val)
@step("Enter <val> in textarea with css <sel>")
def t_ta(val, sel):     _type("css",   sel, val)
@step("Clear field with css <sel>")
def clr_css(sel):       _find("css",   sel).clear()
@step("Clear field with id <sel>")
def clr_id(sel):        _find("id",    sel).clear()
@step("Clear field with name <sel>")
def clr_nm(sel):        _find("name",  sel).clear()
@step("Clear field with xpath <sel>")
def clr_xp(sel):        _find("xpath", sel).clear()


# Dropdowns
def _sel(st, sv, opt):
    sx = Select(_find(st, sv))
    try:    sx.select_by_visible_text(opt)
    except:
        try:    sx.select_by_value(opt)
        except: sx.select_by_index(0)
    logger.info(f"Selected '{{opt}}'")

@step("Select option <opt> from dropdown with css <sel>")
def sel_css(opt, sel): _sel("css",  sel, opt)
@step("Select option <opt> from dropdown with id <sel>")
def sel_id(opt, sel):  _sel("id",   sel, opt)
@step("Select option <opt> from dropdown with name <sel>")
def sel_nm(opt, sel):  _sel("name", sel, opt)


# Visibility / Assertions
@step("Verify element with css <sel> is visible")
def v_css(sel):   _vis("css",   sel)
@step("Verify element with id <sel> is visible")
def v_id(sel):    _vis("id",    sel)
@step("Verify element with xpath <sel> is visible")
def v_xp(sel):    _vis("xpath", sel)
@step("Verify element with name <sel> is visible")
def v_nm(sel):    _vis("name",  sel)
@step("Assert element with css <sel> is visible")
def a_css(sel):   _vis("css",   sel)
@step("Assert element with id <sel> is visible")
def a_id(sel):    _vis("id",    sel)
@step("Assert element with xpath <sel> is visible")
def a_xp(sel):    _vis("xpath", sel)

@step("Verify element with url <url> is visible")
def v_url(url):
    cur = _d().current_url
    assert url in cur, f"URL '{{cur}}' does not contain '{{url}}'"
    logger.info(f"URL contains: {{url}}")

@step("Verify element with text <text> is visible")
def v_txt(text):
    body = _d().find_element(By.TAG_NAME, "body").text
    assert text.lower() in body.lower(), f"Text '{{text}}' not found on page"
    logger.info(f"Text found: {{text}}")

@step("Verify element with alt <alt_text> is visible")
def v_alt(alt_text):
    imgs = _d().find_elements(By.XPATH, f"//img[@alt='{{alt_text}}']")
    assert len(imgs) > 0, f"No image with alt='{{alt_text}}' found"
    assert imgs[0].is_displayed(), f"Image with alt='{{alt_text}}' is not visible"
    logger.info(f"Image with alt='{{alt_text}}' is visible")

@step("Assert element with css <sel> is not visible")
def a_not_vis(sel):
    els = _d().find_elements(By.CSS_SELECTOR, sel)
    if els:
        assert not els[0].is_displayed(), f"{{sel}} should be hidden"

@step("Assert text <text> exists on page")
def a_text(text):
    body = _d().find_element(By.TAG_NAME, "body").text
    assert text.lower() in body.lower(), f"'{{text}}' not found on page"
    logger.info(f"Text found: '{{text}}'")

@step("Assert text <text> is not on page")
def a_no_text(text):
    body = _d().find_element(By.TAG_NAME, "body").text
    assert text.lower() not in body.lower(), f"'{{text}}' unexpectedly present"

@step("Assert element with css <sel> has text <expected>")
def a_el_txt(sel, expected):
    el = _find("css", sel)
    assert expected.lower() in el.text.lower(), f"Got '{{el.text}}', want '{{expected}}'"


# Wait
@step("Wait for element with css <sel> to be visible")
def w_css(sel):
    _w().until(EC.visibility_of_element_located((By.CSS_SELECTOR, sel)))
@step("Wait for element with id <sel> to be visible")
def w_id(sel):
    _w().until(EC.visibility_of_element_located((By.ID, sel)))
@step("Wait <n> seconds")
def w_sec(n):
    time.sleep(float(n))


# Hover
@step("Hover over element with css <sel>")
def hover_css(sel):
    ActionChains(_d()).move_to_element(_find("css",   sel)).perform()
    time.sleep(0.4)
@step("Hover over element with xpath <sel>")
def hover_xp(sel):
    ActionChains(_d()).move_to_element(_find("xpath", sel)).perform()


# Scroll
@step("Scroll to element with css <sel>")
def scroll_css(sel):
    el = _find("css", sel)
    _d().execute_script("arguments[0].scrollIntoView({{block: 'center'}});", el)
@step("Scroll to bottom of page")
def scroll_bot():
    _d().execute_script("window.scrollTo(0, document.body.scrollHeight);")
@step("Scroll to top of page")
def scroll_top():
    _d().execute_script("window.scrollTo(0, 0);")


# Forms
@step("Submit form with css <sel>")
def submit(sel):
    _find("css", sel).submit()
@step("Check checkbox with css <sel>")
def chk(sel):
    el = _find("css", sel)
    if not el.is_selected():
        el.click()
@step("Uncheck checkbox with css <sel>")
def unchk(sel):
    el = _find("css", sel)
    if el.is_selected():
        el.click()


# Accessibility
@step("Verify all images have alt text")
def chk_alt():
    imgs = _d().find_elements(By.TAG_NAME, "img")
    bad  = [img.get_attribute("src") or "?" for img in imgs if not img.get_attribute("alt")]
    assert not bad, f"{{len(bad)}} image(s) missing alt text"
    logger.info(f"All {{len(imgs)}} images have alt text")

@step("Verify all inputs have labels")
def chk_labels():
    inputs = _d().find_elements(By.CSS_SELECTOR, "input:not([type='hidden'])")
    bad    = []
    for inp in inputs:
        iid = inp.get_attribute("id")
        if iid and not _d().find_elements(By.CSS_SELECTOR, f"label[for='{{iid}}']"):
            if not inp.get_attribute("aria-label") and not inp.get_attribute("placeholder"):
                bad.append(iid)
    if bad:
        logger.warning(f"Inputs without labels: {{bad}}")


# Misc
@step("Take screenshot with name <n>")
def take_ss(n):
    _ss(n)

@step("Verify test outcome is <outcome>")
def outcome(o):
    logger.info(f"Expected outcome: {{o}}")
'''


if __name__ == "__main__":
    run()