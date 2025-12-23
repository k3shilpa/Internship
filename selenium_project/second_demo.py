from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Path to your ChromeDriver
service = Service("C:\\drivers\\chromedriver-win64\\chromedriver-win64\\chromedriver.exe")
driver = webdriver.Chrome(service=service)

# Open Google
driver.get("https://www.google.com")

# Wait until search box appears
wait = WebDriverWait(driver, 10)
search_box = wait.until(
    EC.presence_of_element_located((By.NAME, "q"))
)

# Type and search
search_box.send_keys("Selenium with Python")
search_box.submit()

# Wait until title changes
wait.until(EC.title_contains("Selenium"))

print("Page title after search:")
print(driver.title)

driver.quit()
