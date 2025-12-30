import os
import time
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# -----------------------------
# CONFIG
# -----------------------------
TARGET_URL = "https://geeksforgeeks.org"   # 🔹 Change this
OUTPUT_DIR = "web_crawler"
OUTPUT_FILE = "index.html"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# -----------------------------
# Selenium Setup (VISIBLE)
# -----------------------------
chrome_options = Options()
chrome_options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_options
)

print("Opening website...")
driver.get(TARGET_URL)

# Wait for JS (React/Vue) to render
time.sleep(8)

# -----------------------------
# Capture Rendered HTML
# -----------------------------
html = driver.page_source
soup = BeautifulSoup(html, "html.parser")

file_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
with open(file_path, "w", encoding="utf-8") as f:
    f.write(soup.prettify())

print(f"Saved rendered HTML as {file_path}")

# -----------------------------
# Close Browser (VISIBLE)
# -----------------------------
time.sleep(5)
driver.quit()

print("Browser closed")
