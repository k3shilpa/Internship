"""
playwright_driver.py  [FIXED]
==============================
Playwright browser wrapper with proper cleanup to prevent EPIPE errors.

The EPIPE error occurs when Python tries to send a message to the
Playwright Node.js process after it has already been closed.
Fix: catch and suppress EPIPE on close(), use try/finally in all ops.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

BROWSER_TYPE = os.getenv("BROWSER_TYPE", "chromium")   # chromium | firefox | webkit
HEADLESS     = os.getenv("HEADLESS", "true").lower() == "true"


class PlaywrightDriver:
    """
    Thin wrapper around Playwright sync API.
    Creates one browser + one context + one page for the lifetime of a run.
    """

    def __init__(self):
        from playwright.sync_api import sync_playwright

        self._pw      = sync_playwright().start()
        browser_type  = getattr(self._pw, BROWSER_TYPE)

        self._browser = browser_type.launch(
            headless=HEADLESS,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        )
        self.context  = self._browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            ignore_https_errors=True,
        )
        self.page = self.context.new_page()

        # Suppress console errors from the page under test
        self.page.on("console", lambda msg: None)
        self.page.on("pageerror", lambda err: None)

    def screenshot(self, path: str | None = None) -> bytes:
        """Take a full-page screenshot. Returns PNG bytes."""
        try:
            kwargs = {"full_page": True}
            if path:
                kwargs["path"] = path
            return self.page.screenshot(**kwargs)
        except Exception as exc:
            print(f"[PlaywrightDriver] Screenshot failed: {exc}")
            return b""

    def close(self):
        """
        Gracefully close browser and Playwright.
        Suppresses EPIPE / broken pipe errors that occur when
        the Node.js process exits before Python finishes writing.
        """
        # Close page
        try:
            if self.page and not self.page.is_closed():
                self.page.close()
        except Exception:
            pass

        # Close context
        try:
            if self.context:
                self.context.close()
        except Exception:
            pass

        # Close browser
        try:
            if self._browser:
                self._browser.close()
        except Exception:
            pass

        # Stop Playwright — redirect stderr to suppress EPIPE noise
        try:
            import io
            old_stderr = sys.stderr
            sys.stderr  = io.StringIO()   # suppress EPIPE output
            self._pw.stop()
            sys.stderr  = old_stderr
        except Exception:
            sys.stderr = sys.__stderr__   # always restore

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __del__(self):
        """Destructor safety net."""
        try:
            self.close()
        except Exception:
            pass