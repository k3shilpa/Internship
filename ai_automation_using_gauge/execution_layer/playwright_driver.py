"""
Playwright Driver Wrapper
Handles Browser initialisation for Chromium, Firefox, or WebKit.
"""

from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

BROWSER_TYPE = os.getenv("PLAYWRIGHT_BROWSER", "chromium").lower()
HEADLESS     = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true"
SLOW_MO      = int(os.getenv("PLAYWRIGHT_SLOW_MO", 0))
TIMEOUT      = int(os.getenv("PLAYWRIGHT_TIMEOUT", 30000))


class PlaywrightDriver:
    """Manages a Playwright browser + page instance."""

    def __init__(self):
        from playwright.sync_api import sync_playwright
        self._pw     = sync_playwright().start()
        self.browser = self._launch_browser()
        self.context = self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            ignore_https_errors=True,
        )
        self.page = self.context.new_page()
        self.page.set_default_timeout(TIMEOUT)

    def _launch_browser(self):
        opts = {"headless": HEADLESS, "slow_mo": SLOW_MO}
        if BROWSER_TYPE == "firefox":
            return self._pw.firefox.launch(**opts)
        elif BROWSER_TYPE in ("webkit", "safari"):
            return self._pw.webkit.launch(**opts)
        else:
            return self._pw.chromium.launch(**opts)

    def screenshot(self, path: str) -> bool:
        try:
            self.page.screenshot(path=path, full_page=True)
            return True
        except Exception:
            return False

    def close(self):
        try:
            self.context.close()
            self.browser.close()
            self._pw.stop()
        except Exception:
            pass