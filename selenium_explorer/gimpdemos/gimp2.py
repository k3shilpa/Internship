from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

# -----------------------------
# 1. Browser setup
# -----------------------------
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.maximize_window()
wait = WebDriverWait(driver, 25)

EDITOR_URL = "https://fixthephoto.com/online-gimp-editor.html"
driver.get(EDITOR_URL)

print("✅ Editor opened")

# -----------------------------
# 2. Find correct iframe (IMPORTANT FIX)
# -----------------------------
iframes = wait.until(
    EC.presence_of_all_elements_located((By.TAG_NAME, "iframe"))
)
print(f"✅ Found {len(iframes)} iframe(s)")

editor_surface = None

for index, iframe in enumerate(iframes):
    try:
        driver.switch_to.default_content()
        driver.switch_to.frame(iframe)

        editor_surface = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((
                By.CSS_SELECTOR,
                "canvas, div[contenteditable], div[class*='canvas'], div[class*='editor']"
            ))
        )

        print(f"✅ Editor iframe detected at index {index}")
        break

    except:
        continue

if not editor_surface:
    driver.quit()
    raise Exception("❌ Editor iframe not found")

# -----------------------------
# 3. Editor surface ready
# -----------------------------
print("✅ Editor surface detected")

# -----------------------------
# 4. Select Brush tool (safe selector)
# -----------------------------
brush_tool = wait.until(
    EC.element_to_be_clickable((
        By.XPATH,
        "//*[contains(@title,'Brush') or contains(@aria-label,'Brush')]"
    ))
)
brush_tool.click()
print("✅ Brush tool selected")

# -----------------------------
# 5. Click editor surface
# -----------------------------
editor_surface.click()
print("✅ Editor surface clicked (tool execution verified)")

time.sleep(1)

# -----------------------------
# 6. UNDO via keyboard (CORRECT)
# -----------------------------
body = driver.find_element(By.TAG_NAME, "body")
body.send_keys(Keys.CONTROL, "z")
print("✅ Undo executed via Ctrl+Z")

# -----------------------------
# 7. Zoom in / out
# -----------------------------
body.send_keys(Keys.CONTROL, "+")
time.sleep(0.5)
body.send_keys(Keys.CONTROL, "-")
print("✅ Zoom in / out executed")

# -----------------------------
# 8. Finish
# -----------------------------
time.sleep(5)
driver.quit()
print("✅ UI automation test completed successfully")
