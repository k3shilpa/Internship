from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# Start Chrome
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

# Open web form
driver.get("https://www.selenium.dev/selenium/web/web-form.html")

# Find text box and type
text_box = driver.find_element(By.NAME, "my-text")
text_box.send_keys("Reading text example")

# Find submit button and click
submit_button = driver.find_element(By.CSS_SELECTOR, "button")
submit_button.click()

# Find the message text on result page
message = driver.find_element(By.ID, "message")

# Read and print the text
print("Message on page:", message.text)

# Wait so you can see the page
input("Press Enter to close browser...")

# Close browser
driver.quit()
