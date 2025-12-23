from selenium import webdriver
from selenium.webdriver.chrome.service import Service

service = Service("C:\\drivers\\chromedriver-win64\\chromedriver-win64\\chromedriver.exe")
driver = webdriver.Chrome(service=service)

driver.get("https://www.google.com")
print("Chrome opened successfully!")

driver.quit()

