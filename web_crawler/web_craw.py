import os
import time
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# -----------------------------
# CONFIGURATION
# -----------------------------
#TARGET_URL = "https://geeksforgeeks.org"   # 🔹 Change this
TARGET_URL = "https://seleniumbase.io/demo_page_with_menu_items/"
OUTPUT_DIR = "frontend_code_dynamic"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# -----------------------------
# Setup Selenium
# -----------------------------
chrome_options = Options()
#chrome_options.add_argument("--headless")  # Remove this if you want to see browser
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_options
)

print("Opening website...")
driver.get(TARGET_URL)

# Wait for JS rendering (React/Vue)
time.sleep(5)

# -----------------------------
# Get Rendered HTML
# -----------------------------
html = driver.page_source
soup = BeautifulSoup(html, "html.parser")

# Save HTML
html_path = os.path.join(OUTPUT_DIR, "index.html")
with open(html_path, "w", encoding="utf-8") as f:
    f.write(soup.prettify())

print("Saved rendered HTML")

# -----------------------------
# Helper function to save assets
# -----------------------------
def save_asset(url, folder):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        filename = os.path.basename(urlparse(url).path)
        if not filename:
            return

        file_path = os.path.join(folder, filename)

        with open(file_path, "wb") as f:
            f.write(response.content)

        print(f"Saved: {file_path}")

    except Exception as e:
        print(f"Failed: {url} -> {e}")

# -----------------------------
# Extract CSS files
# -----------------------------
css_dir = os.path.join(OUTPUT_DIR, "css")
os.makedirs(css_dir, exist_ok=True)

for link in soup.find_all("link", rel="stylesheet"):
    href = link.get("href")
    if href:
        full_url = urljoin(TARGET_URL, href)
        save_asset(full_url, css_dir)

# -----------------------------
# Extract JavaScript files
# -----------------------------
js_dir = os.path.join(OUTPUT_DIR, "js")
os.makedirs(js_dir, exist_ok=True)

for script in soup.find_all("script"):
    src = script.get("src")
    if src:
        full_url = urljoin(TARGET_URL, src)
        save_asset(full_url, js_dir)

# -----------------------------
# Cleanup
# -----------------------------
driver.quit()
print("\nDynamic frontend extraction completed.")
