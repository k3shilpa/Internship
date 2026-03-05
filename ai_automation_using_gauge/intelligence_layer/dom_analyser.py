"""
dom_analyser.py  [FIXED - Timeout]
===================================
Multi-page DOM Analyzer using Playwright with robust timeout handling.

Fix: Sites with heavy ads/trackers never reach 'networkidle'.
     Now uses a waterfall of wait strategies:
       1. networkidle  (ideal)
       2. load         (fallback)
       3. domcontentloaded (last resort)
     Each with configurable timeout.

Config (.env):
    CRAWLER_MAX_PAGES        = 5
    CRAWLER_MAX_DEPTH        = 2
    CRAWLER_SAME_DOMAIN      = true
    CRAWLER_TIMEOUT          = 30000   per-page timeout ms
    CRAWLER_WAIT_UNTIL       = load    wait strategy: networkidle|load|domcontentloaded
"""

from __future__ import annotations

import os
import sys
import time
from collections import deque
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

MAX_PAGES    = int(os.getenv("CRAWLER_MAX_PAGES",   5))
MAX_DEPTH    = int(os.getenv("CRAWLER_MAX_DEPTH",   2))
SAME_DOMAIN  = os.getenv("CRAWLER_SAME_DOMAIN", "true").lower() == "true"
PAGE_TIMEOUT = int(os.getenv("CRAWLER_TIMEOUT",  30000))
WAIT_UNTIL   = os.getenv("CRAWLER_WAIT_UNTIL", "load")   # changed default to "load"

sys.path.insert(0, str(Path(__file__).parent.parent))

_driver_instance = None


def _get_driver():
    global _driver_instance
    if _driver_instance is None:
        from execution_layer.playwright_driver import PlaywrightDriver
        _driver_instance = PlaywrightDriver()
    return _driver_instance


def _normalize(url: str) -> str:
    return urlparse(url)._replace(fragment="").geturl().rstrip("/")


def _same_domain(url: str, base: str) -> bool:
    return urlparse(url).netloc == urlparse(base).netloc


def _crawlable(url: str, base: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https", ""):
        return False
    skip_exts = {
        ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp",
        ".mp4", ".mp3", ".zip", ".css", ".js", ".ico",
        ".woff", ".woff2", ".ttf", ".exe", ".dmg",
    }
    if any(parsed.path.lower().endswith(e) for e in skip_exts):
        return False
    if parsed.scheme in ("mailto", "tel", "javascript"):
        return False
    if SAME_DOMAIN and parsed.netloc and not _same_domain(url, base):
        return False
    return True


# ─────────────────────────────────────────────────────────────────────────────
# Robust page loader — tries multiple wait strategies
# ─────────────────────────────────────────────────────────────────────────────

def _load_page(page, url: str, timeout: int) -> bool:
    """
    Try loading a page with progressively more lenient wait strategies.
    Returns True if page loaded successfully, False if all strategies failed.
    """
    strategies = ["load", "domcontentloaded"]

    # If user configured networkidle, try it first
    if WAIT_UNTIL == "networkidle":
        strategies = ["networkidle", "load", "domcontentloaded"]

    for strategy in strategies:
        try:
            page.goto(url, wait_until=strategy, timeout=timeout)
            # Extra small wait for JS to render initial content
            time.sleep(1.0)
            print(f"[DOMAnalyzer] Loaded ({strategy}): {url}")
            return True
        except Exception as exc:
            err = str(exc)[:80]
            print(f"[DOMAnalyzer] '{strategy}' failed for {url}: {err}")
            continue

    return False


# ─────────────────────────────────────────────────────────────────────────────
# Single-page DOM extractor
# ─────────────────────────────────────────────────────────────────────────────

class _PageExtractor:
    def __init__(self, url: str, soup: BeautifulSoup):
        self.url  = url
        self.soup = soup

    def extract(self) -> dict:
        forms    = self._forms()
        inputs   = self._inputs()
        buttons  = self._buttons()
        links    = self._links()
        headings = self._headings()
        title    = self.soup.title.get_text(strip=True) if self.soup.title else ""
        return {
            "url":      self.url,
            "title":    title,
            "forms":    forms,
            "inputs":   inputs,
            "buttons":  buttons,
            "links":    links,
            "headings": headings,
            "summary":  self._summary(title, forms, inputs, buttons, links, headings),
        }

    def _forms(self):
        forms = []
        for form in self.soup.find_all("form"):
            fields = [
                {
                    "tag":         f.name,
                    "type":        f.get("type", "text"),
                    "name":        f.get("name", ""),
                    "id":          f.get("id", ""),
                    "placeholder": f.get("placeholder", ""),
                    "required":    f.has_attr("required"),
                }
                for f in form.find_all(["input", "select", "textarea"])
            ]
            forms.append({
                "id":     form.get("id", ""),
                "action": form.get("action", ""),
                "method": form.get("method", "get").upper(),
                "fields": fields,
            })
        return forms

    def _inputs(self):
        return [
            {
                "type":        el.get("type", "text"),
                "name":        el.get("name", ""),
                "id":          el.get("id", ""),
                "placeholder": el.get("placeholder", ""),
                "required":    el.has_attr("required"),
                "aria_label":  el.get("aria-label", ""),
            }
            for el in self.soup.find_all("input")
        ]

    def _buttons(self):
        buttons = []
        for el in self.soup.find_all(["button", "input"]):
            if el.name == "button" or el.get("type") in ("submit", "button", "reset"):
                buttons.append({
                    "tag":        el.name,
                    "type":       el.get("type", "button"),
                    "text":       el.get_text(strip=True)[:80],
                    "id":         el.get("id", ""),
                    "aria_label": el.get("aria-label", ""),
                })
        return buttons

    def _links(self):
        links = []
        for el in self.soup.find_all("a", href=True):
            href = el["href"].strip()
            if href:
                links.append({
                    "text":       el.get_text(strip=True)[:60],
                    "href":       urljoin(self.url, href),
                    "aria_label": el.get("aria-label", ""),
                })
        return links

    def _headings(self):
        headings = []
        for tag in ["h1", "h2", "h3"]:
            for el in self.soup.find_all(tag):
                text = el.get_text(strip=True)
                if text:
                    headings.append(f"[{tag.upper()}] {text}")
        return headings

    def _summary(self, title, forms, inputs, buttons, links, headings) -> str:
        lines = [
            f"Page    : {self.url}",
            f"Title   : {title}",
            f"Forms={len(forms)} | Inputs={len(inputs)} | "
            f"Buttons={len(buttons)} | Links={len(links)}",
        ]
        if headings:
            lines.append("Headings: " + " | ".join(headings[:5]))
        if forms:
            for f in forms:
                names = [
                    fld["name"] or fld["id"]
                    for fld in f["fields"]
                    if fld["name"] or fld["id"]
                ]
                lines.append(f"  Form[{f['method']}] fields={names}")
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Multi-page BFS crawler
# ─────────────────────────────────────────────────────────────────────────────

class DOMAnalyzer:
    """
    BFS crawler with configurable page limit, depth limit, and
    robust timeout handling for ad-heavy / JS-heavy sites.

    Parameters
    ----------
    url         : Entry-point URL
    max_pages   : Max total pages   (default: CRAWLER_MAX_PAGES)
    max_depth   : Max crawl depth   (default: CRAWLER_MAX_DEPTH)
    same_domain : Same-domain only  (default: CRAWLER_SAME_DOMAIN)
    timeout     : Per-page ms       (default: CRAWLER_TIMEOUT)
    """

    def __init__(
        self,
        url:         str,
        max_pages:   int  = MAX_PAGES,
        max_depth:   int  = MAX_DEPTH,
        same_domain: bool = SAME_DOMAIN,
        timeout:     int  = PAGE_TIMEOUT,
    ):
        self.start_url   = url
        self.max_pages   = max_pages
        self.max_depth   = max_depth
        self.same_domain = same_domain
        self.timeout     = timeout
        self._visited:   set[str]   = set()
        self._pages:     list[dict] = []
        self._queue:     deque      = deque()

    # ── Public ────────────────────────────────────────────────────────────────

    def extract(self) -> dict[str, Any]:
        print(f"\n[DOMAnalyzer] Start: {self.start_url}")
        print(f"[DOMAnalyzer] Limits -> max_pages={self.max_pages}  "
              f"max_depth={self.max_depth}  same_domain={self.same_domain}")
        print(f"[DOMAnalyzer] Timeout: {self.timeout}ms  "
              f"wait_until: {WAIT_UNTIL} (with fallback)")

        self._crawl()

        if not self._pages:
            raise RuntimeError(
                f"No pages could be crawled from {self.start_url}\n"
                "Try setting CRAWLER_WAIT_UNTIL=domcontentloaded in .env\n"
                "or CRAWLER_TIMEOUT=60000 for slow sites"
            )

        result = self._merge()
        print(f"[DOMAnalyzer] Complete -> {len(self._visited)} pages visited\n")
        return result

    # ── BFS ───────────────────────────────────────────────────────────────────

    def _crawl(self):
        self._queue.append((_normalize(self.start_url), 0))

        while self._queue:
            if len(self._visited) >= self.max_pages:
                print(f"[DOMAnalyzer] Page limit ({self.max_pages}) reached.")
                break

            url, depth = self._queue.popleft()

            if url in self._visited:
                continue
            if depth > self.max_depth:
                print(f"[DOMAnalyzer] Depth limit {self.max_depth} exceeded: {url}")
                continue

            print(f"[DOMAnalyzer] [{len(self._visited)+1}/{self.max_pages}] "
                  f"depth={depth}/{self.max_depth}  {url}")

            page_data = self._visit(url)
            if page_data is None:
                continue

            self._visited.add(url)
            self._pages.append(page_data)

            if depth < self.max_depth:
                remaining = self.max_pages - len(self._visited)
                added     = 0
                for link in page_data["links"]:
                    if added >= remaining:
                        break
                    href = link.get("href", "")
                    if not href:
                        continue
                    norm = _normalize(href)
                    if (
                        norm not in self._visited
                        and _crawlable(href, self.start_url)
                        and (not self.same_domain
                             or _same_domain(href, self.start_url))
                    ):
                        self._queue.append((norm, depth + 1))
                        added += 1

    def _visit(self, url: str) -> dict | None:
        try:
            page = _get_driver().page

            # Abort unnecessary resource types to speed up loading
            page.route(
                "**/*",
                lambda route: route.abort()
                if route.request.resource_type in
                   ("image", "media", "font", "stylesheet")
                else route.continue_()
            )

            ok = _load_page(page, url, self.timeout)
            if not ok:
                print(f"[DOMAnalyzer] All load strategies failed: {url}")
                return None

            # Unregister route handlers for next page
            page.unroute("**/*")

            soup = BeautifulSoup(page.content(), "lxml")
            return _PageExtractor(url, soup).extract()

        except Exception as exc:
            print(f"[DOMAnalyzer] SKIP {url}  reason: {exc}")
            try:
                page.unroute("**/*")
            except Exception:
                pass
            return None

    # ── Merge ─────────────────────────────────────────────────────────────────

    def _merge(self) -> dict[str, Any]:
        first = self._pages[0]
        all_forms, all_inputs, all_buttons = [], [], []
        all_links, all_headings = [], []

        for pg in self._pages:
            src = pg["url"]
            all_forms.extend({**f, "_source_url": src}   for f in pg["forms"])
            all_inputs.extend({**i, "_source_url": src}  for i in pg["inputs"])
            all_buttons.extend({**b, "_source_url": src} for b in pg["buttons"])
            all_links.extend({**l, "_source_url": src}   for l in pg["links"])
            all_headings.extend(pg["headings"])

        seen, unique_links = set(), []
        for lnk in all_links:
            if lnk["href"] not in seen:
                seen.add(lnk["href"])
                unique_links.append(lnk)

        return {
            "url":               self.start_url,
            "page_title":        first["title"],
            "summary":           self._combined_summary(first),
            "forms":             all_forms,
            "inputs":            all_inputs,
            "buttons":           all_buttons,
            "links":             unique_links[:100],
            "headings":          all_headings,
            "pages":             self._pages,
            "pages_visited":     len(self._visited),
            "max_depth_reached": min(self.max_depth, len(self._visited)),
            "crawl_config": {
                "max_pages":   self.max_pages,
                "max_depth":   self.max_depth,
                "same_domain": self.same_domain,
                "timeout_ms":  self.timeout,
                "wait_until":  WAIT_UNTIL,
            },
        }

    def _combined_summary(self, first: dict) -> str:
        t_forms   = sum(len(p["forms"])   for p in self._pages)
        t_inputs  = sum(len(p["inputs"])  for p in self._pages)
        t_buttons = sum(len(p["buttons"]) for p in self._pages)
        t_links   = sum(len(p["links"])   for p in self._pages)

        lines = [
            f"Entry URL    : {self.start_url}",
            f"Page Title   : {first['title']}",
            f"Pages Crawled: {len(self._pages)}  "
            f"(limit={self.max_pages}, depth_limit={self.max_depth})",
            f"Totals: Forms={t_forms}  Inputs={t_inputs}  "
            f"Buttons={t_buttons}  Links={t_links}",
            "",
            "Pages Visited:",
        ]
        for pg in self._pages:
            lines.append(
                f"  {pg['url']}  "
                f"[forms={len(pg['forms'])} "
                f"inputs={len(pg['inputs'])} "
                f"buttons={len(pg['buttons'])}]"
            )
        if first["headings"]:
            lines += ["", "Headings (first page):"]
            lines.extend(first["headings"][:6])
        if first["forms"]:
            lines += ["", "Forms (first page):"]
            for f in first["forms"]:
                names = [fld["name"] or fld["id"] for fld in f["fields"]]
                lines.append(
                    f"  id='{f['id']}' [{f['method']}] "
                    f"action='{f['action']}' fields={names}"
                )
        return "\n".join(lines)