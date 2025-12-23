from selenium import webdriver
from selenium.webdriver.chrome.service import Service
driver = webdriver.Chrome(service=Service("C:\\drivers\\chromedriver-win64\\chromedriver-win64\\chromedriver.exe"))
driver.get("https://www.google.com")
print("Chrome opened successfully!")
input("Press ENTER to close the browser...")
driver.quit()