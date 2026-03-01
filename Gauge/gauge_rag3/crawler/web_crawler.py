"""
crawler/web_crawler.py
======================
Crawls a website and saves extracted element metadata to a JSON file.

HOW TO RUN (from the project root folder):
    python crawler/web_crawler.py

ALL SETTINGS ARE HARDCODED BELOW — edit the values and run.
No config file, no CLI arguments, no relative imports.
"""

import json
import time
import logging
import os
from datetime import datetime
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# =============================================================================
#  SETTINGS — edit these values directly
# =============================================================================

TARGET_URL      = "https://www.calculator.net/"             # website to crawl
MAX_PAGES       = 5                                 # max pages to visit
MAX_DEPTH       = 2                                   # how deep to follow links
HEADLESS        = True                                # False = show browser window
WAIT_AFTER_LOAD = 2                                   # seconds to wait for JS after page load
PAGE_TIMEOUT    = 30                                  # seconds before giving up on a page

OUTPUT_FILE     = "data/metadata/metadata.json"       # where to save results

# =============================================================================

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)


# ── Element extraction helpers (all in one file, no imports needed) ───────────

def _safe(el, attr):
    try:
        v = el.get_attribute(attr)
        return v.strip() if v else ""
    except:
        return ""

def _selector(el):
    if v := _safe(el, "id"):          return {"type": "id",   "value": v}
    if v := _safe(el, "name"):        return {"type": "name", "value": v}
    if v := _safe(el, "data-testid"): return {"type": "css",  "value": f"[data-testid='{v}']"}
    if v := _safe(el, "aria-label"):  return {"type": "css",  "value": f"[aria-label='{v}']"}
    try:
        tag = el.tag_name
        cls = _safe(el, "class")
        return {"type": "css", "value": f"{tag}.{cls.split()[0]}"} if cls else {"type": "xpath", "value": f"//{tag}"}
    except:
        return {"type": "xpath", "value": "//unknown"}

def _desc(el):
    try:
        tag  = el.tag_name
        text = el.text.strip()[:50] if el.text else ""
        ph   = _safe(el, "placeholder")
        aria = _safe(el, "aria-label")
        tp   = _safe(el, "type")
        p    = [f"<{tag}"]
        if tp:     p.append(f" type='{tp}'")
        if text:   p.append(f"> '{text}'")
        elif ph:   p.append(f" placeholder='{ph}'>")
        elif aria: p.append(f" aria-label='{aria}'>")
        else:      p.append(">")
        return "".join(p)
    except:
        return "unknown"

def extract_interactive(driver):
    items = []
    for btn in driver.find_elements(By.TAG_NAME, "button"):
        try:
            if not btn.is_displayed(): continue
            items.append({"element_type": "button", "text": btn.text.strip()[:80],
                          "selector": _selector(btn), "description": _desc(btn),
                          "disabled": _safe(btn, "disabled") == "true",
                          "type": _safe(btn, "type") or "button"})
        except: continue
    for inp in driver.find_elements(By.CSS_SELECTOR, "input[type='button'],input[type='submit'],input[type='reset']"):
        try:
            if not inp.is_displayed(): continue
            items.append({"element_type": "input_button", "text": _safe(inp, "value"),
                          "selector": _selector(inp), "description": _desc(inp), "type": _safe(inp, "type")})
        except: continue
    return items

def extract_navigation(driver):
    items = []; seen = set()
    for a in driver.find_elements(By.TAG_NAME, "a"):
        try:
            if not a.is_displayed(): continue
            href = _safe(a, "href")
            if not href or href in seen: continue
            if any(href.startswith(p) for p in ["javascript:", "mailto:"]): continue
            seen.add(href)
            items.append({"element_type": "link", "text": a.text.strip()[:80], "href": href,
                          "selector": _selector(a), "description": _desc(a),
                          "target": _safe(a, "target"), "is_external": _is_external(driver.current_url, href)})
        except: continue
    return items

def extract_forms(driver):
    forms = []
    for i, form in enumerate(driver.find_elements(By.TAG_NAME, "form")):
        try:
            fd = {"element_type": "form", "form_index": i, "action": _safe(form, "action"),
                  "method": _safe(form, "method") or "GET", "selector": _selector(form),
                  "fields": [], "submit_buttons": []}
            for inp in form.find_elements(By.TAG_NAME, "input"):
                t = _safe(inp, "type") or "text"
                if t == "hidden": continue
                if t in ["submit", "button", "reset"]:
                    fd["submit_buttons"].append({"type": t, "value": _safe(inp, "value"), "selector": _selector(inp)}); continue
                fd["fields"].append({"element_type": f"input_{t}", "input_type": t,
                    "name": _safe(inp, "name"), "id": _safe(inp, "id"),
                    "placeholder": _safe(inp, "placeholder"),
                    "required": _safe(inp, "required") in ["true", ""],
                    "selector": _selector(inp), "label": _label(driver, inp), "description": _desc(inp),
                    "validation": {k: v for k, v in {
                        "minlength": _safe(inp, "minlength"), "maxlength": _safe(inp, "maxlength"),
                        "pattern": _safe(inp, "pattern"), "min": _safe(inp, "min"), "max": _safe(inp, "max")
                    }.items() if v}})
            for ta in form.find_elements(By.TAG_NAME, "textarea"):
                fd["fields"].append({"element_type": "textarea", "name": _safe(ta, "name"),
                    "placeholder": _safe(ta, "placeholder"),
                    "required": _safe(ta, "required") in ["true", ""],
                    "selector": _selector(ta), "label": _label(driver, ta), "description": _desc(ta)})
            for sel in form.find_elements(By.TAG_NAME, "select"):
                opts = [{"text": o.text.strip(), "value": _safe(o, "value")} for o in sel.find_elements(By.TAG_NAME, "option")]
                fd["fields"].append({"element_type": "select", "name": _safe(sel, "name"),
                    "required": _safe(sel, "required") in ["true", ""],
                    "selector": _selector(sel), "label": _label(driver, sel),
                    "options": opts[:20], "description": _desc(sel)})
            for btn in form.find_elements(By.CSS_SELECTOR, "button[type='submit'],button:not([type])"):
                fd["submit_buttons"].append({"type": "submit", "text": btn.text.strip(), "selector": _selector(btn)})
            forms.append(fd)
        except: continue
    return forms

def extract_media(driver):
    items = []
    for img in driver.find_elements(By.TAG_NAME, "img"):
        try:
            if not img.is_displayed(): continue
            items.append({"element_type": "image", "src": _safe(img, "src"), "alt": _safe(img, "alt"),
                          "has_alt": bool(_safe(img, "alt")), "selector": _selector(img)})
        except: continue
    return items

def extract_content(driver):
    items = []
    for tag in ["h1", "h2", "h3", "h4"]:
        for h in driver.find_elements(By.TAG_NAME, tag):
            try:
                text = h.text.strip()
                if text: items.append({"element_type": "heading", "level": tag, "text": text[:100], "selector": _selector(h)})
            except: continue
    return items

def extract_tables(driver):
    items = []
    for i, tbl in enumerate(driver.find_elements(By.TAG_NAME, "table")):
        try:
            headers = [th.text.strip() for th in tbl.find_elements(By.TAG_NAME, "th")]
            rows    = len(tbl.find_elements(By.TAG_NAME, "tr"))
            items.append({"element_type": "table", "table_index": i, "headers": headers,
                          "row_count": rows, "selector": _selector(tbl)})
        except: continue
    return items

def _label(driver, el):
    try:
        el_id = _safe(el, "id")
        if el_id:
            ls = driver.find_elements(By.CSS_SELECTOR, f"label[for='{el_id}']")
            if ls: return ls[0].text.strip()
        p = el.find_element(By.XPATH, "..")
        if p.tag_name == "label": return p.text.strip()[:60]
    except: pass
    return ""

def _is_external(current, href):
    try:
        return urlparse(href).netloc not in ("", urlparse(current).netloc)
    except:
        return False


# ── Crawler ───────────────────────────────────────────────────────────────────

class WebCrawler:
    def __init__(self):
        self.domain  = urlparse(TARGET_URL).netloc
        self.visited = set()
        self.pages   = []
        self.driver  = None

    def _start_driver(self):
        opts = Options()
        if HEADLESS:
            opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--window-size=1920,1080")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36")
        svc = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=svc, options=opts)
        self.driver.set_page_load_timeout(PAGE_TIMEOUT)

    def run(self):
        logger.info(f"\n{'='*55}")
        logger.info(f"CRAWLER  |  {TARGET_URL}")
        logger.info(f"pages={MAX_PAGES}  depth={MAX_DEPTH}  headless={HEADLESS}")
        logger.info(f"output → {OUTPUT_FILE}")
        logger.info(f"{'='*55}")

        self._start_driver()
        try:
            self._visit(TARGET_URL, 0)
        finally:
            self.driver.quit()

        metadata = {
            "crawl_metadata": {
                "base_url":   TARGET_URL,
                "pages":      len(self.pages),
                "crawled_at": datetime.now().isoformat(),
            },
            "pages": self.pages,
            "summary": {
                "total_interactive": sum(len(p["elements"]["interactive"]) for p in self.pages),
                "total_forms":       sum(len(p["elements"]["forms"])       for p in self.pages),
                "total_links":       sum(len(p["elements"]["navigation"])  for p in self.pages),
                "total_tables":      sum(len(p["elements"]["tables"])      for p in self.pages),
                "page_types":        list(set(p["page_type"] for p in self.pages)),
            }
        }

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"\nDone — {len(self.pages)} page(s) crawled")
        logger.info(f"Saved → {OUTPUT_FILE}")
        logger.info(f"\nNext step: python rag/embedder.py")

    def _visit(self, url, depth):
        if url in self.visited or len(self.visited) >= MAX_PAGES: return
        if depth > MAX_DEPTH or not self._same_domain(url): return

        logger.info(f"  [depth={depth}] {url}")
        self.visited.add(url)
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, PAGE_TIMEOUT).until(
                EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(WAIT_AFTER_LOAD)
            self._scroll()
            self.pages.append(self._extract(url))
            if depth < MAX_DEPTH:
                for link in self._collect_links():
                    self._visit(link, depth + 1)
        except TimeoutException:
            logger.warning(f"  Timeout: {url}")
        except WebDriverException as e:
            logger.warning(f"  Error: {str(e)[:80]}")

    def _extract(self, url):
        ctx = (url + self.driver.title).lower()
        if   any(k in ctx for k in ["cart","checkout","payment"]): ptype = "ecommerce_checkout"
        elif any(k in ctx for k in ["product","shop","buy","price"]): ptype = "ecommerce_product"
        elif any(k in ctx for k in ["contact","signup","register","login"]): ptype = "form_page"
        elif any(k in ctx for k in ["blog","article","news"]): ptype = "content_page"
        elif any(k in ctx for k in ["about","team","company"]): ptype = "informational"
        else: ptype = "general"

        page = {
            "url": url, "title": self.driver.title,
            "crawled_at": datetime.now().isoformat(), "page_type": ptype,
            "elements": {
                "interactive": extract_interactive(self.driver),
                "navigation":  extract_navigation(self.driver),
                "forms":       extract_forms(self.driver),
                "media":       extract_media(self.driver),
                "content":     extract_content(self.driver),
                "tables":      extract_tables(self.driver),
            }
        }
        total = sum(len(v) for v in page["elements"].values())
        logger.info(f"    {total} elements extracted")
        return page

    def _collect_links(self):
        hrefs = []
        try:
            for a in self.driver.find_elements(By.TAG_NAME, "a"):
                href = a.get_attribute("href")
                if href and self._valid_link(href):
                    hrefs.append(href)
        except: pass
        return list(set(hrefs))

    def _valid_link(self, href):
        if any(href.lower().endswith(e) for e in [".pdf",".jpg",".png",".gif",".zip",".mp4",".svg"]): return False
        if any(href.startswith(p) for p in ["#","mailto:","tel:","javascript:"]): return False
        return self._same_domain(href)

    def _same_domain(self, url):
        try: return urlparse(url).netloc in (self.domain, "")
        except: return False

    def _scroll(self):
        try:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(0.4)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.4)
            self.driver.execute_script("window.scrollTo(0, 0);")
        except: pass


if __name__ == "__main__":
    WebCrawler().run()