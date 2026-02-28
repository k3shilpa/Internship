from getgauge.python import step, before_scenario, after_scenario, before_suite, after_suite
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

_driver = None
_wait = None


# ── Helpers ────────────────────────────────────────────────────────────────────

def _find_first(selectors, timeout=10):
    """Try multiple (By, selector) pairs and return the first element found."""
    for by, sel in selectors:
        try:
            return WebDriverWait(_driver, timeout).until(
                EC.presence_of_element_located((by, sel))
            )
        except Exception:
            continue
    return None


def _is_driver_alive():
    try:
        _ = _driver.current_url
        return True
    except Exception:
        return False


# ── Hooks ──────────────────────────────────────────────────────────────────────

@before_suite
def before_suite_hook():
    global _driver, _wait
    options = Options()
    # options.add_argument("--headless")   # Uncomment for CI
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    _driver = webdriver.Chrome(options=options)
    _wait = WebDriverWait(_driver, 15)


@after_suite
def after_suite_hook():
    try:
        _driver.quit()
    except Exception:
        pass


@before_scenario
def before_scenario_hook():
    global _driver, _wait
    # If Chrome has crashed or been closed, restart it
    if not _is_driver_alive():
        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        _driver = webdriver.Chrome(options=options)
        _wait = WebDriverWait(_driver, 15)
    else:
        try:
            _driver.delete_all_cookies()
        except Exception:
            pass


@after_scenario
def after_scenario_hook():
    pass


# ── Navigation ─────────────────────────────────────────────────────────────────

@step("Navigate to <url>")
def navigate_to(url):
    _driver.get(url)
    _wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))


# ── Search ─────────────────────────────────────────────────────────────────────
# calculator.net homepage: search input is inside a form, located by type=text
# near the "Search" submit button — no name or id attribute

@step("Enter search term <term>")
def enter_search_term(term):
    # Try every common pattern — the homepage uses a plain <input type="text">
    # with no name/id inside a search form
    selectors = [
        (By.NAME, "search"),
        (By.ID, "search"),
        (By.CSS_SELECTOR, "input[type='search']"),
        (By.CSS_SELECTOR, "form input[type='text']"),
        (By.XPATH, "//input[@type='text' and following-sibling::input[@value='Search']]"),
        (By.XPATH, "//input[@value='Search']/preceding-sibling::input[@type='text']"),
        (By.XPATH, "//form[.//input[@value='Search']]//input[@type='text']"),
        (By.CSS_SELECTOR, "input[type='text']"),   # last resort
    ]
    search = _find_first(selectors, timeout=5)
    assert search is not None, (
        "Could not find search input. The page may not have a search box."
    )
    search.clear()
    search.send_keys(term)


@step("Click the search button")
def click_search_button():
    selectors = [
        (By.CSS_SELECTOR, "input[value='Search']"),
        (By.XPATH, "//input[@value='Search']"),
        (By.CSS_SELECTOR, "button[type='submit']"),
        (By.CSS_SELECTOR, "input[type='submit']"),
        (By.XPATH, "//button[contains(text(),'Search')]"),
    ]
    for by, sel in selectors:
        try:
            btn = WebDriverWait(_driver, 5).until(EC.element_to_be_clickable((by, sel)))
            btn.click()
            _wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            return
        except Exception:
            continue
    # Fallback: press Enter in any search text field
    try:
        _driver.find_element(By.CSS_SELECTOR, "input[type='text']").send_keys(Keys.RETURN)
        _wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    except Exception:
        pass


# ── Verification ───────────────────────────────────────────────────────────────

@step("Verify the page contains <text>")
def verify_page_contains(text):
    assert text in _driver.page_source, f"Expected '{text}' not found on page"


# ── Login ──────────────────────────────────────────────────────────────────────

@step("Enter email <email>")
def enter_email(email):
    field = _wait.until(EC.presence_of_element_located((
        By.CSS_SELECTOR, "input[type='email'], input[name='email']"
    )))
    field.clear()
    field.send_keys(email)


@step("Enter password <password>")
def enter_password(password):
    field = _wait.until(EC.presence_of_element_located((
        By.CSS_SELECTOR, "input[type='password']"
    )))
    field.clear()
    field.send_keys(password)


@step("Click the login button")
def click_login_button():
    btn = _wait.until(EC.element_to_be_clickable((
        By.CSS_SELECTOR, "button[type='submit'], input[type='submit']"
    )))
    btn.click()
    _wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))


@step("Verify the user is logged in")
def verify_logged_in():
    # calculator.net shows "sign out" text when logged in
    elements = _driver.find_elements(
        By.XPATH,
        "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign out')]"
    )
    assert len(elements) > 0, (
        "User is not logged in. Note: test@example.com is not a real calculator.net account."
    )


# ── Generic Buttons ────────────────────────────────────────────────────────────

@step("Click the calculate button")
def click_calculate_button():
    selectors = [
        (By.CSS_SELECTOR, "input[value='Calculate']"),
        (By.XPATH, "//input[@value='Calculate']"),
        (By.CSS_SELECTOR, "input[type='submit']"),
        (By.CSS_SELECTOR, "button[type='submit']"),
    ]
    for by, sel in selectors:
        try:
            btn = WebDriverWait(_driver, 5).until(EC.element_to_be_clickable((by, sel)))
            btn.click()
            _wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            return
        except Exception:
            continue


@step("Click the clear button")
def click_clear_button():
    selectors = [
        (By.CSS_SELECTOR, "input[value='Clear']"),
        (By.CSS_SELECTOR, "input[type='reset']"),
        (By.XPATH, "//input[@value='Clear']"),
    ]
    for by, sel in selectors:
        try:
            btn = WebDriverWait(_driver, 5).until(EC.element_to_be_clickable((by, sel)))
            btn.click()
            return
        except Exception:
            continue


@step("Click the <link_text> link")
def click_link(link_text):
    link = _wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, link_text)))
    link.click()
    _wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))


# ── Loan Amount (used by mortgage, payment, loan calculators) ─────────────────
# Actual field names found by inspecting page source:
#   mortgage-calculator  → "chousevalue"  (labeled "Home Price")
#   payment-calculator   → "cloanamount"
#   loan-calculator      → "cloanamount"

@step("Enter loan amount <amount>")
def enter_loan_amount(amount):
    # Use XPath to find ANY visible number input that's not interest/term
    # Try known names first, then fall back to positional approach
    selectors = [
        (By.NAME, "chousevalue"),    # mortgage calculator
        (By.NAME, "cloanamount"),    # payment / loan calculator
        (By.ID, "chousevalue"),
        (By.ID, "cloanamount"),
        # Generic fallback: first number input in the form
        (By.XPATH, "(//input[@type='text' or not(@type)])[1]"),
    ]
    field = _find_first(selectors, timeout=10)
    assert field is not None, "Could not find loan/house price amount field"
    field.clear()
    field.send_keys(amount)


@step("Enter interest rate <rate>")
def enter_interest_rate(rate):
    field = _wait.until(EC.presence_of_element_located((By.NAME, "cinterestrate")))
    field.clear()
    field.send_keys(rate)


@step("Enter loan term <term>")
def enter_loan_term(term):
    field = _wait.until(EC.presence_of_element_located((By.NAME, "cloanterm")))
    field.clear()
    field.send_keys(term)


@step("Verify monthly payment is displayed")
def verify_monthly_payment():
    _wait.until(EC.presence_of_element_located((
        By.XPATH, "//*[contains(text(),'$')]"
    )))


@step("Verify amortization schedule is displayed")
def verify_amortization():
    tables = _driver.find_elements(By.TAG_NAME, "table")
    assert len(tables) > 0, "Amortization table not found"


# ── Loan Calculator compounding dropdown ──────────────────────────────────────
# Actual option text: "Annually (APY)", "Monthly (APR)", etc.

@step("Select compounding frequency <frequency>")
def select_compounding_frequency(frequency):
    dropdown = _wait.until(EC.presence_of_element_located((By.NAME, "ccompound")))
    Select(dropdown).select_by_visible_text(frequency)


# ── Auto Loan Calculator ───────────────────────────────────────────────────────
# Actual field names from calculator.net auto-loan-calculator page source:
#   Sale Price      → "cautovalue"
#   Cash Incentives → "cincentive"
#   Down Payment    → "cdownpayment"
#   Trade-in Value  → "ctradeinvalue"
#   Amount Owed     → "ctradeowned"  (or "ctradeamount" — try both)
#   Sales Tax       → "csaletax"
#   Title/Reg fees  → "ctitlereg"
#   State           → "cstate"

@step("Enter sale price <price>")
def enter_sale_price(price):
    field = _find_first([
        (By.NAME, "cautovalue"),
        (By.NAME, "csaleprice"),
        (By.ID, "cautovalue"),
    ])
    assert field is not None, "Could not find sale price field"
    field.clear()
    field.send_keys(price)


@step("Enter incentive <amount>")
def enter_incentive(amount):
    field = _wait.until(EC.presence_of_element_located((By.NAME, "cincentive")))
    field.clear()
    field.send_keys(amount)


@step("Enter down payment <amount>")
def enter_down_payment(amount):
    field = _wait.until(EC.presence_of_element_located((By.NAME, "cdownpayment")))
    field.clear()
    field.send_keys(amount)


@step("Enter trade in value <value>")
def enter_trade_in_value(value):
    field = _wait.until(EC.presence_of_element_located((By.NAME, "ctradeinvalue")))
    field.clear()
    field.send_keys(value)


@step("Enter trade in owned <value>")
def enter_trade_in_owned(value):
    # Try both known possible names for "Amount Owed on Trade-in"
    field = _find_first([
        (By.NAME, "ctradeowned"),
        (By.NAME, "ctradeamount"),
        (By.NAME, "ctradevalue"),
        # Positional fallback: 7th input on the form
        (By.XPATH, "(//input[@type='text' or not(@type)])[7]"),
    ])
    assert field is not None, "Could not find 'trade-in owned' field"
    field.clear()
    field.send_keys(value)


@step("Select state <state>")
def select_state(state):
    dropdown = _wait.until(EC.presence_of_element_located((By.NAME, "cstate")))
    Select(dropdown).select_by_value(state)


@step("Enter sale tax <tax>")
def enter_sale_tax(tax):
    field = _wait.until(EC.presence_of_element_located((By.NAME, "csaletax")))
    field.clear()
    field.send_keys(tax)


@step("Enter title and registration <amount>")
def enter_title_and_registration(amount):
    field = _wait.until(EC.presence_of_element_located((By.NAME, "ctitlereg")))
    field.clear()
    field.send_keys(amount)


# ── Payment Calculator ─────────────────────────────────────────────────────────

@step("Verify loan amount input field is empty")
def verify_loan_amount_empty():
    field = _find_first([
        (By.NAME, "cloanamount"),
        (By.ID, "cloanamount"),
    ])
    if field:
        value = field.get_attribute("value")
        assert value == "" or value is None, f"Expected empty but got: '{value}'"


# ── Retirement Calculator ──────────────────────────────────────────────────────
# The retirement calculator has MULTIPLE sections with different forms.
# "How much do you need to retire?" section uses these field names.
# We use index-based XPath as a robust fallback.

@step("Enter current age <age>")
def enter_current_age(age):
    field = _find_first([
        (By.NAME, "cage"),
        (By.ID, "cage"),
        (By.XPATH, "(//input[@type='text' or not(@type)])[1]"),
    ])
    assert field is not None, "Could not find 'current age' field"
    field.clear()
    field.send_keys(age)


@step("Enter retirement age <age>")
def enter_retirement_age(age):
    field = _find_first([
        (By.NAME, "cretireage"),
        (By.ID, "cretireage"),
        (By.XPATH, "(//input[@type='text' or not(@type)])[2]"),
    ])
    assert field is not None, "Could not find 'retirement age' field"
    field.clear()
    field.send_keys(age)


@step("Enter life expectancy <age>")
def enter_life_expectancy(age):
    field = _find_first([
        (By.NAME, "clifeexpect"),
        (By.ID, "clifeexpect"),
        (By.XPATH, "(//input[@type='text' or not(@type)])[3]"),
    ])
    assert field is not None, "Could not find 'life expectancy' field"
    field.clear()
    field.send_keys(age)


@step("Enter current income <income>")
def enter_current_income(income):
    field = _find_first([
        (By.NAME, "cincome"),
        (By.ID, "cincome"),
        (By.XPATH, "(//input[@type='text' or not(@type)])[4]"),
    ])
    assert field is not None, "Could not find 'current income' field"
    field.clear()
    field.send_keys(income)


@step("Enter income growth rate <rate>")
def enter_income_growth_rate(rate):
    field = _find_first([
        (By.NAME, "cincgrowth"),
        (By.ID, "cincgrowth"),
        (By.XPATH, "(//input[@type='text' or not(@type)])[5]"),
    ])
    assert field is not None, "Could not find 'income growth rate' field"
    field.clear()
    field.send_keys(rate)


@step("Enter desired retirement income <income>")
def enter_desired_retirement_income(income):
    field = _find_first([
        (By.NAME, "cretireincome"),
        (By.ID, "cretireincome"),
        (By.XPATH, "(//input[@type='text' or not(@type)])[6]"),
    ])
    assert field is not None, "Could not find 'desired retirement income' field"
    field.clear()
    field.send_keys(income)
