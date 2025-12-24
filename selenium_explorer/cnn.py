from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
from transformers import pipeline


summarizer = pipeline(
    "summarization",
    model="facebook/bart-large-cnn",
    device=-1
)


driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
wait = WebDriverWait(driver, 10)

driver.get("https://edition.cnn.com/")
wait.until(EC.presence_of_element_located((By.TAG_NAME, "a")))


def summarize_text(text):
    if not text.strip() or len(text) < 300:
        return "Not enough article content to summarize"

    text = text[:2000]  

    summary = summarizer(
        text,
        max_length=150,
        min_length=60,
        do_sample=False
    )

    return summary[0]["summary_text"]


visited_links = set()

# CNN article URLs usually contain /YYYY/MM/DD/
article_pattern = re.compile(r"/\d{4}/\d{2}/\d{2}/")

for step in range(10):
    print("\n")
    #print(f"\n🔹 STEP {step + 1}")

    links = driver.find_elements(By.TAG_NAME, "a")
    next_url = None

    
    for link in links:
        url = link.get_attribute("href")

        if not url:
            continue
        if "cnn.com" not in url:
            continue
        if not article_pattern.search(url):
            continue
        if url in visited_links:
            continue
        if any(x in url for x in ["/videos", "/watch", "/shorts", "/live"]):
            continue

        next_url = url
        break

    if not next_url:
        print("No new article link found")
        break

    print("Opening:", next_url)
    visited_links.add(next_url)

    driver.get(next_url)

    try:
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "p")))
    except:
        print("⚠ Page loaded but no readable content")
        continue

    
    paragraphs = driver.find_elements(By.TAG_NAME, "p")
    article_text = " ".join(p.text for p in paragraphs if p.text.strip())

    #print(" Extracted characters:", len(article_text))

    if len(article_text) < 300:
        print("Skipping page (not a valid article)")
        continue

   
    summary = summarize_text(article_text)

    print("\n SUMMARY:")
    print(summary)
    print("-" * 80)


driver.quit()
