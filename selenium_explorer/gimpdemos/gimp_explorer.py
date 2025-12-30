from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import time

# -----------------------------
# Setup
# -----------------------------
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.maximize_window()
actions = ActionChains(driver)

URL = "https://fixthephoto.com/online-gimp-editor.html"
driver.get(URL)
time.sleep(7)

print("Editor Loaded")

# -----------------------------
# Focus the editor
# -----------------------------
body = driver.find_element(By.TAG_NAME, "body")
body.click()
time.sleep(1)

# -----------------------------
# Keyboard-based menu exploration
# -----------------------------
menus = [
    Keys.ALT + "f",  # File
    Keys.ALT + "e",  # Edit
    Keys.ALT + "i",  # Image
    Keys.ALT + "l",  # Layer
    Keys.ALT + "s",  # Select
    Keys.ALT + "v",  # View
    Keys.ALT + "t",  # Tools
    Keys.ALT + "c",  # Colors
    Keys.ALT + "h",  # Help
]

for key in menus:
    print(f"🔹 Opening menu: {key}")
    actions.key_down(Keys.ALT).send_keys(key[-1]).key_up(Keys.ALT).perform()
    time.sleep(2)

    # Navigate inside menu
    for _ in range(5):
        actions.send_keys(Keys.ARROW_DOWN).perform()
        time.sleep(0.5)

    actions.send_keys(Keys.ESCAPE).perform()
    time.sleep(1)

print("✅ Keyboard menu exploration complete")
driver.quit()
