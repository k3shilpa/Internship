from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# Start Chrome browser
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

# Open the web form page
driver.get("https://www.selenium.dev/selenium/web/web-form.html")

# Find the text box using its name attribute
text_box = driver.find_element(By.NAME, "my-text")

# Type text into the box
text_box.send_keys("Hello Selenium!")

# Find the submit button
submit_button = driver.find_element(By.CSS_SELECTOR, "button")

# Click the submit button
submit_button.click()

# Wait so you can see the result
input("Press Enter to close browser...")

# Close browser
driver.quit()

