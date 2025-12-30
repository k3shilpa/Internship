from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
    NoSuchWindowException
)
import time


driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.maximize_window()
wait = WebDriverWait(driver, 10)

#BASE_URL = "https://www.w3schools.com"
#BASE_URL = "https://demo.opencart.com"
BASE_URL = "https://seleniumbase.io/demo_page_with_menu_items/"
driver.get(BASE_URL)
time.sleep(0.5)

MAIN_WINDOW = driver.current_window_handle
print("Opened website")


def get_clickable_links():
    valid_links = []

    try:
        links = driver.find_elements(By.TAG_NAME, "a")
    except NoSuchWindowException:
        return valid_links

    for link in links:
        try:
            href = link.get_attribute("href")
            if href and href.startswith("http"):
                valid_links.append(href)
        except (StaleElementReferenceException, NoSuchWindowException):
            continue

    return list(set(valid_links))



visited = set()
all_links = get_clickable_links()

print(f"Found {len(all_links)} links")

for link in all_links:
    if link in visited:
        continue

    print(f"\nVisiting: {link}")
    visited.add(link)

    try:
        driver.get(link)
        time.sleep(0.5)

        # Handle new tabs/windows
        for window in driver.window_handles:
            if window != MAIN_WINDOW:
                driver.switch_to.window(window)
                driver.close()

        driver.switch_to.window(MAIN_WINDOW)

    except (TimeoutException, NoSuchWindowException):
        print("Window issue detected, recovering...")
        try:
            driver.switch_to.window(MAIN_WINDOW)
        except NoSuchWindowException:
            print("Main window closed, reopening browser")
            driver.quit()
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
            driver.get(BASE_URL)
            MAIN_WINDOW = driver.current_window_handle
            time.sleep(0.5)

    # Re-collect links (DOM changes!)
    all_links = get_clickable_links()

print("\nFinished exploring all menus")
driver.quit()
