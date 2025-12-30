from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from transformers import pipeline
from urllib.parse import urlparse
import time

# ------------------------------------
# STEP 1: Starting URL (hardcoded)
# ------------------------------------
#start_url = "https://www.tutorialspoint.com/java/index.htm"
#start_url = "https://en.wikipedia.org/wiki/Data_structure"
#start_url = "https://edition.cnn.com/world"
start_url = "https://plato.stanford.edu/"


#start_url = "https://www.theguardian.com/international"
# You can change this to ANY website

summarizer = pipeline(
    "summarization",
    model="facebook/bart-large-cnn",
    device=-1  # CPU only
)


driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
wait = WebDriverWait(driver, 15)

current_url = start_url
visited_links = set()
start_domain = urlparse(start_url).netloc

MAX_CHARS = 1000   # 🔹 LIMIT EXTRACTION (FAST)


def summarize_text(text):
    if len(text) < 80:
        return "Not enough content to summarize"

    summary = summarizer(
        text,
        max_length=120,
        min_length=50,
        do_sample=False
    )
    return summary[0]["summary_text"]


for step in range(10):
    print(f"\n{step + 1}")
    print("Opening:", current_url)

    driver.get(current_url)

   
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

   
    page_text = ""
    paragraphs = driver.find_elements(By.TAG_NAME, "p")

    for p in paragraphs:
        try:
            txt = p.text.strip()
            if txt:
                page_text += txt + " "

            if len(page_text) >= MAX_CHARS:
                page_text = page_text[:MAX_CHARS]
                break
        except:
            continue

    #print("📄 Characters extracted:", len(page_text))

    summary = summarize_text(page_text)
    print("\n SUMMARY:")
    print(summary)
    print("-" * 70)

    visited_links.add(current_url)

    
    next_url = None
    links = driver.find_elements(By.TAG_NAME, "a")

    for link in links:
        try:
            url = link.get_attribute("href")
        except:
            continue

        if not url:
            continue
        if "#" in url:
            continue
        if not url.startswith("http"):
            continue
        if url in visited_links:
            continue
        if start_domain not in url:
            continue
        if any(x in url.lower() for x in ["login", "signup", "video", "image"]):
            continue

        next_url = url
        break

    if not next_url:
        print("❌ No next valid link found. Stopping.")
        break

    current_url = next_url


driver.quit()
