# ===== crawler/crawler.py =====

import json
from pathlib import Path
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# -------------------------------------------------
# CONFIG
# -------------------------------------------------

START_URL = "https://www.calculator.net/"
MAX_DEPTH = 1
MAX_PAGES = 8
WAIT_TIMEOUT = 10

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = DATA_DIR / "elements.json"


# -------------------------------------------------
# DRIVER
# -------------------------------------------------

def get_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-gpu")
    options.add_argument("--log-level=3")
    return webdriver.Chrome(options=options)


# -------------------------------------------------
# STABLE LOCATOR GENERATION
# -------------------------------------------------

def get_locator(driver, element):

    element_id = element.get_attribute("id")
    if element_id:
        return f"//*[@id='{element_id}']"

    element_name = element.get_attribute("name")
    if element_name:
        return f"//*[@name='{element_name}']"

    # Fallback: absolute XPath
    return driver.execute_script("""
    function absoluteXPath(element) {
      if (element.id !== '')
        return "//*[@id='" + element.id + "']";
      if (element === document.body)
        return '/html/body';

      var ix = 0;
      var siblings = element.parentNode.childNodes;
      for (var i = 0; i < siblings.length; i++) {
        var sibling = siblings[i];
        if (sibling === element)
          return absoluteXPath(element.parentNode) + '/' +
                 element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
        if (sibling.nodeType === 1 &&
            sibling.tagName === element.tagName)
          ix++;
      }
    }
    return absoluteXPath(arguments[0]);
    """, element)


# -------------------------------------------------
# LABEL DETECTION (Final Refined Version)
# -------------------------------------------------

def get_label(driver, element):

    element_id = element.get_attribute("id")

    # 1️⃣ <label for="">
    if element_id:
        labels = driver.find_elements(By.XPATH, f"//label[@for='{element_id}']")
        if labels and labels[0].text.strip():
            return labels[0].text.strip()

    # 2️⃣ aria-label
    aria = element.get_attribute("aria-label")
    if aria:
        return aria.strip()

    # 3️⃣ placeholder
    placeholder = element.get_attribute("placeholder")
    if placeholder:
        return placeholder.strip()

    # 4️⃣ Try td[1] direct text nodes only
    try:
        td1 = element.find_element(By.XPATH, "ancestor::tr[1]/td[1]")

        text = driver.execute_script("""
        var node = arguments[0];
        var text = "";
        for (var i = 0; i < node.childNodes.length; i++) {
            if (node.childNodes[i].nodeType === Node.TEXT_NODE) {
                text += node.childNodes[i].textContent;
            }
        }
        return text;
        """, td1)

        text = text.strip()

        if text and len(text) < 120:
            return text

    except:
        pass

    # 5️⃣ If td[1] empty, try td[2] direct text nodes
    try:
        td2 = element.find_element(By.XPATH, "ancestor::tr[1]/td[2]")

        text = driver.execute_script("""
        var node = arguments[0];
        var text = "";
        for (var i = 0; i < node.childNodes.length; i++) {
            if (node.childNodes[i].nodeType === Node.TEXT_NODE) {
                text += node.childNodes[i].textContent;
            }
        }
        return text;
        """, td2)

        text = text.strip()

        if text and len(text) < 120:
            return text

    except:
        pass

    # 6️⃣ Previous sibling fallback
    try:
        sibling = element.find_element(By.XPATH, "preceding-sibling::*[1]")
        if sibling.text.strip():
            return sibling.text.strip()
    except:
        pass

    return ""


# -------------------------------------------------
# FIELD EXTRACTION
# -------------------------------------------------

def extract_field(driver, element):

    tag = element.tag_name.lower()
    input_type = (element.get_attribute("type") or "").lower()

    if input_type in ["hidden", "file", "reset", "image"]:
        return None

    options = []
    if tag == "select":
        for opt in element.find_elements(By.TAG_NAME, "option"):
            text = opt.text.strip()
            if text:
                options.append(text)

    return {
        "tag": tag,
        "type": input_type,
        "label": get_label(driver, element),
        "id": element.get_attribute("id"),
        "name": element.get_attribute("name"),
        "placeholder": element.get_attribute("placeholder"),
        "min": element.get_attribute("min"),
        "max": element.get_attribute("max"),
        "step": element.get_attribute("step"),
        "options": options,
        "locator": get_locator(driver, element)
    }


# -------------------------------------------------
# PAGE EXTRACTION
# -------------------------------------------------

def extract_page(driver, url):

    forms_data = []
    seen_locators = set()

    forms = driver.find_elements(By.TAG_NAME, "form")

    for form in forms:

        fields = []
        submit_buttons = []

        elements = form.find_elements(
            By.XPATH,
            ".//input | .//textarea | .//select | .//button"
        )

        for el in elements:

            if not el.is_displayed():
                continue

            tag = el.tag_name.lower()
            input_type = (el.get_attribute("type") or "").lower()

            locator = get_locator(driver, el)

            if locator in seen_locators:
                continue

            seen_locators.add(locator)

            if input_type in ["submit", "button"] or tag == "button":
                submit_buttons.append({
                    "locator": locator,
                    "text": el.text.strip()
                })
                continue

            field = extract_field(driver, el)
            if field:
                fields.append(field)

        if fields:
            forms_data.append({
                "fields": fields,
                "submit_buttons": submit_buttons
            })

    return {
        "page_url": url,
        "title": driver.title,
        "forms": forms_data
    }


# -------------------------------------------------
# CRAWLER
# -------------------------------------------------

def crawl():

    driver = get_driver()
    visited = set()
    results = []

    base_domain = urlparse(START_URL).netloc

    def dfs(url, depth):

        if depth > MAX_DEPTH:
            return
        if url in visited:
            return
        if len(results) >= MAX_PAGES:
            return

        visited.add(url)

        print(f"🔎 Crawling: {url}")
        driver.get(url)

        WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        page_data = extract_page(driver, url)

        if page_data["forms"]:
            results.append(page_data)

        links = driver.find_elements(By.TAG_NAME, "a")
        hrefs = set()

        for link in links:
            try:
                href = link.get_attribute("href")
                if href and urlparse(href).netloc == base_domain:
                    hrefs.add(href.split("#")[0])
            except:
                continue

        for href in hrefs:
            dfs(href, depth + 1)

    dfs(START_URL, 0)

    OUTPUT_FILE.write_text(
        json.dumps(results, indent=2),
        encoding="utf-8"
    )

    print("✅ elements.json generated successfully")
    driver.quit()


# -------------------------------------------------
# ENTRY
# -------------------------------------------------

if __name__ == "__main__":
    crawl()
