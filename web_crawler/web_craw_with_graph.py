from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from collections import deque
from urllib.parse import urljoin
import networkx as nx
import matplotlib.pyplot as plt
import json
import time
import os

# -----------------------------
# CONFIG
# -----------------------------
#START_URL = "https://books.toscrape.com/"
#START_URL = "https://docs.google.com/"
START_URL = "https://www.calculator.net/"
MAX_DEPTH = 2
MAX_PAGES = 20
PAGE_LOAD_WAIT = 2

OUTPUT_DIR = r"D:/Internship/web_crawler"
OUTPUT_JSON = os.path.join(OUTPUT_DIR, "clickables.json")

# -----------------------------
# HELPER: GET XPATH
# -----------------------------
def get_xpath(driver, element):
    return driver.execute_script(
        """
        function absoluteXPath(element) {
            if (element === document.body)
                return '/html/body';
            let ix = 0;
            let siblings = element.parentNode.childNodes;
            for (let i = 0; i < siblings.length; i++) {
                let sibling = siblings[i];
                if (sibling === element)
                    return absoluteXPath(element.parentNode) + '/' +
                           element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                if (sibling.nodeType === 1 && sibling.tagName === element.tagName)
                    ix++;
            }
        }
        return absoluteXPath(arguments[0]);
        """,
        element
    )

# -----------------------------
# COLLECT CLICKABLES FROM PAGE
# -----------------------------
def collect_clickables(driver):
    clickables = []
    elements = []

    elements.extend(driver.find_elements(By.TAG_NAME, "a"))
    elements.extend(driver.find_elements(By.TAG_NAME, "button"))
    elements.extend(driver.find_elements(
        By.XPATH,
        "//input[@type='button' or @type='submit' or @type='radio' or @type='checkbox']"
    ))
    elements.extend(driver.find_elements(By.TAG_NAME, "select"))
    elements.extend(driver.find_elements(By.XPATH, "//*[@onclick or @role='button' or @tabindex]"))

    seen = set()

    for el in elements:
        try:
            if not el.is_displayed() or not el.is_enabled():
                continue

            key = (el.tag_name, el.text.strip(), el.get_attribute("href"))
            if key in seen:
                continue
            seen.add(key)

            clickables.append({
                "tag": el.tag_name,
                "text": el.text.strip(),
                "href": el.get_attribute("href"),
                "id": el.get_attribute("id"),
                "class": el.get_attribute("class"),
                "name": el.get_attribute("name"),
                "xpath": get_xpath(driver, el)
            })

        except Exception:
            continue

    return clickables

# -----------------------------
# SELENIUM CRAWLER
# -----------------------------
def crawl_and_collect(start_url):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--log-level=3")

    driver = webdriver.Chrome(options=options)

    visited = set()
    queue = deque([(start_url, 0)])
    results = []
    graph = nx.DiGraph()

    print("🚀 Selenium crawl started")

    while queue:
        current_url, depth = queue.popleft()

        if current_url in visited or depth > MAX_DEPTH or len(visited) >= MAX_PAGES:
            continue

        print(f"🌐 Visiting: {current_url} (Depth {depth})")
        visited.add(current_url)

        try:
            driver.get(current_url)
            time.sleep(PAGE_LOAD_WAIT)

            clickables = collect_clickables(driver)

            results.append({
                "url": current_url,
                "clickables": clickables
            })

            # Self-loop (page references itself)
            graph.add_edge(current_url, current_url)

            # Crawl links + build graph
            for a in driver.find_elements(By.TAG_NAME, "a"):
                href = a.get_attribute("href")
                if href:
                    next_url = urljoin(current_url, href)
                    graph.add_edge(current_url, next_url)

                    if next_url not in visited:
                        queue.append((next_url, depth + 1))

        except Exception as e:
            print(f"⚠️ Error visiting {current_url}: {e}")

    driver.quit()
    return results, graph

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    data, graph = crawl_and_collect(START_URL)

    # Save JSON
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n Clickables saved to {OUTPUT_JSON}")
    print(f" Pages processed: {len(data)}")
    print(f" Graph nodes: {graph.number_of_nodes()}")
    print(f" Graph edges: {graph.number_of_edges()}")

    # -----------------------------
    # GRAPH VISUALIZATION
    # -----------------------------
    if graph.number_of_nodes() > 0:
        plt.figure(figsize=(20, 20))
        pos = nx.spring_layout(graph, seed=42, k=0.15, iterations=60)

        nx.draw(
            graph,
            pos,
            with_labels=True,
            node_size=120,
            font_size=7,
            arrows=True,
            arrowstyle="->",
            width=0.6
        )

        plt.title("Website Navigation Graph (Selenium)", fontsize=16)
        plt.show()
