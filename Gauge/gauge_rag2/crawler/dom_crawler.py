# crawler/dom_crawler.py - DOM Crawler using Selenium + Chrome

import json
import logging
import time
from urllib.parse import urljoin, urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logger = logging.getLogger(__name__)


def _build_driver() -> webdriver.Chrome:
    opts = Options()
    if config.CHROME_HEADLESS:
        opts.add_argument("--headless=new")
    opts.add_argument(f"--window-size={config.CHROME_WINDOW_SIZE}")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    driver = webdriver.Chrome(options=opts)
    driver.implicitly_wait(config.IMPLICIT_WAIT)
    driver.set_page_load_timeout(config.PAGE_LOAD_TIMEOUT)
    return driver


def _extract_page_dom(driver: webdriver.Chrome, url: str) -> dict:
    """Extract structured DOM data from the current page."""
    logger.info(f"Extracting DOM from: {url}")

    page_data = {
        "url": url,
        "title": driver.title,
        "forms": [],
        "inputs": [],
        "buttons": [],
        "links": [],
        "navigation": [],
        "interactive_elements": [],
        "page_structure": {},
    }

    # ── Forms ────────────────────────────────────────────────────────────────
    forms = driver.find_elements(By.TAG_NAME, "form")
    for i, form in enumerate(forms):
        form_data = {
            "index": i,
            "id": form.get_attribute("id") or "",
            "action": form.get_attribute("action") or "",
            "method": form.get_attribute("method") or "get",
            "fields": [],
        }
        for field in form.find_elements(By.CSS_SELECTOR, "input, select, textarea"):
            form_data["fields"].append(_extract_field_info(field))
        page_data["forms"].append(form_data)

    # ── All Inputs (including those outside forms) ────────────────────────────
    for el in driver.find_elements(By.CSS_SELECTOR, "input, select, textarea"):
        page_data["inputs"].append(_extract_field_info(el))

    # ── Buttons ───────────────────────────────────────────────────────────────
    for btn in driver.find_elements(By.CSS_SELECTOR, "button, input[type='submit'], input[type='button'], [role='button']"):
        page_data["buttons"].append({
            "tag": btn.tag_name,
            "text": btn.text.strip() or btn.get_attribute("value") or "",
            "type": btn.get_attribute("type") or "",
            "id": btn.get_attribute("id") or "",
            "class": btn.get_attribute("class") or "",
            "aria_label": btn.get_attribute("aria-label") or "",
            "visible": btn.is_displayed(),
        })

    # ── Navigation Links ──────────────────────────────────────────────────────
    base_origin = urlparse(url).netloc
    for a in driver.find_elements(By.TAG_NAME, "a"):
        href = a.get_attribute("href") or ""
        is_internal = href and urlparse(href).netloc in ("", base_origin)
        link_info = {
            "text": a.text.strip(),
            "href": href,
            "internal": is_internal,
            "id": a.get_attribute("id") or "",
        }
        page_data["links"].append(link_info)
        if is_internal and href:
            page_data["navigation"].append(href)

    # ── Page Structure (headings, landmark roles) ─────────────────────────────
    headings = {}
    for level in range(1, 7):
        els = driver.find_elements(By.TAG_NAME, f"h{level}")
        if els:
            headings[f"h{level}"] = [e.text.strip() for e in els if e.text.strip()]
    page_data["page_structure"]["headings"] = headings

    # ── Interactive Elements (dropdowns, modals, tabs) ────────────────────────
    for sel in ["[role='tab']", "[role='dialog']", "[role='listbox']", ".dropdown", ".modal"]:
        els = driver.find_elements(By.CSS_SELECTOR, sel)
        for el in els:
            page_data["interactive_elements"].append({
                "selector": sel,
                "text": el.text.strip()[:100],
                "visible": el.is_displayed(),
            })

    return page_data


def _extract_field_info(el) -> dict:
    return {
        "tag": el.tag_name,
        "type": el.get_attribute("type") or "",
        "id": el.get_attribute("id") or "",
        "name": el.get_attribute("name") or "",
        "placeholder": el.get_attribute("placeholder") or "",
        "label": el.get_attribute("aria-label") or "",
        "required": el.get_attribute("required") is not None,
        "value": el.get_attribute("value") or "",
        "class": el.get_attribute("class") or "",
        "visible": el.is_displayed(),
        "pattern": el.get_attribute("pattern") or "",
        "min": el.get_attribute("min") or "",
        "max": el.get_attribute("max") or "",
        "maxlength": el.get_attribute("maxlength") or "",
    }


def crawl(start_url: str = None, max_depth: int = None, max_pages: int = None) -> list[dict]:
    """
    Crawl the target site and return a list of page DOM snapshots.
    Saves results to config.DOM_DATA_PATH.
    """
    start_url = start_url or config.TARGET_URL
    max_depth = max_depth or config.MAX_CRAWL_DEPTH
    max_pages = max_pages or config.MAX_PAGES

    logger.info(f"Starting crawl: {start_url} (depth={max_depth}, max_pages={max_pages})")

    visited = set()
    queue   = [(start_url, 0)]
    results = []

    driver = _build_driver()
    try:
        while queue and len(results) < max_pages:
            url, depth = queue.pop(0)
            if url in visited or depth > max_depth:
                continue
            visited.add(url)

            try:
                driver.get(url)
                time.sleep(1.5)  # allow JS to settle
                page_data = _extract_page_dom(driver, url)
                page_data["crawl_depth"] = depth
                results.append(page_data)
                logger.info(f"  ✓ Crawled [{depth}]: {url}  ({len(page_data['forms'])} forms, {len(page_data['inputs'])} inputs)")

                # Enqueue internal links for next depth
                if depth < max_depth:
                    for nav_url in page_data["navigation"]:
                        if nav_url not in visited:
                            queue.append((nav_url, depth + 1))

            except Exception as e:
                logger.warning(f"  ✗ Failed to crawl {url}: {e}")

    finally:
        driver.quit()

    # Persist
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(config.DOM_DATA_PATH, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Crawl complete. {len(results)} pages saved to {config.DOM_DATA_PATH}")
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    crawl()
