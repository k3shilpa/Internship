# execution/webdriver_initializer.py - Selenium Chrome WebDriver factory

import logging
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

logger = logging.getLogger(__name__)

_driver_instance = None


def get_driver() -> webdriver.Chrome:
    """Return a singleton Chrome WebDriver instance."""
    global _driver_instance
    if _driver_instance is None:
        _driver_instance = _create_driver()
    return _driver_instance


def _create_driver() -> webdriver.Chrome:
    opts = Options()
    if config.CHROME_HEADLESS:
        opts.add_argument("--headless=new")
    opts.add_argument(f"--window-size={config.CHROME_WINDOW_SIZE}")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=opts)
    driver.implicitly_wait(config.IMPLICIT_WAIT)
    driver.set_page_load_timeout(config.PAGE_LOAD_TIMEOUT)
    logger.info("✓ Chrome WebDriver initialised.")
    return driver


def quit_driver():
    """Quit and clean up the WebDriver."""
    global _driver_instance
    if _driver_instance:
        try:
            _driver_instance.quit()
        except Exception:
            pass
        _driver_instance = None
        logger.info("WebDriver closed.")
