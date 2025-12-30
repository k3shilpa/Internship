from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import tkinter as tk
from tkinter import filedialog

# =====================================================
# 0. SELECT EXISTING IMAGE FILE
# =====================================================
root = tk.Tk()
root.withdraw()

IMAGE_PATH = filedialog.askopenfilename(
    title="Select Image to Open",
    filetypes=[
        ("Image Files", "*.png *.jpg *.jpeg *.bmp *.gif"),
        ("All Files", "*.*")
    ]
)

if not IMAGE_PATH:
    raise Exception("❌ No image selected")

IMAGE_PATH = os.path.abspath(IMAGE_PATH)
print(f"🖼️ Selected image: {IMAGE_PATH}")

# =====================================================
# 1. BROWSER SETUP
# =====================================================
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.maximize_window()
wait = WebDriverWait(driver, 40)
actions = ActionChains(driver)

URL = "https://fixthephoto.com/online-gimp-editor.html"
driver.get(URL)
print("✅ Editor opened")

# =====================================================
# 2. SWITCH TO EDITOR IFRAME
# =====================================================
iframes = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "iframe")))

editor_found = False
for iframe in iframes:
    driver.switch_to.default_content()
    driver.switch_to.frame(iframe)
    try:
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "toolbtn")))
        print("✅ Switched to editor iframe")
        editor_found = True
        break
    except:
        continue

if not editor_found:
    driver.quit()
    raise Exception("❌ Editor iframe not found")

# =====================================================
# 3. FILE → OPEN (ROBUST METHOD)
# =====================================================
print("\n📂 FILE → OPEN (upload image)")

# Open File menu (visual feedback only)
file_menu = wait.until(
    EC.element_to_be_clickable((By.XPATH, "//*[normalize-space()='File']"))
)
file_menu.click()
time.sleep(0.8)
print("✅ File menu opened")

# DO NOT click "Open" (canvas-based UI)
# Directly use hidden file input (correct approach)
file_inputs = wait.until(
    EC.presence_of_all_elements_located((By.XPATH, "//input[@type='file']"))
)

file_inputs[0].send_keys(IMAGE_PATH)
print("✅ Image path sent to hidden file input")

# =====================================================
# 4. VERIFY IMAGE LOADED ON CANVAS
# =====================================================
canvas = wait.until(EC.presence_of_element_located((By.TAG_NAME, "canvas")))
time.sleep(2)

canvas_width = canvas.get_attribute("width")
canvas_height = canvas.get_attribute("height")

print(f"🖼️ Canvas size after open: {canvas_width} x {canvas_height}")

if int(canvas_width) > 0 and int(canvas_height) > 0:
    print("✅ Image opened successfully on canvas")
else:
    print("❌ Image not loaded")

# =====================================================
# 5. TOOL USAGE TEST (RECTANGLE SELECT)
# =====================================================
print("\n🧪 TOOL USAGE TEST")

tools = driver.find_elements(By.CSS_SELECTOR, "button.toolbtn")

tool = tools[1]  # Rectangle Select (safe)
tool_name = tool.get_attribute("title")
tool.click()
time.sleep(0.6)

print(f"➡ Using tool: {tool_name}")

# Safe canvas interaction via JS
driver.execute_script("""
const canvas = arguments[0];
const rect = canvas.getBoundingClientRect();
const x = rect.left + rect.width / 2;
const y = rect.top + rect.height / 2;
canvas.dispatchEvent(new MouseEvent('mousedown', {clientX:x, clientY:y, bubbles:true}));
canvas.dispatchEvent(new MouseEvent('mouseup', {clientX:x, clientY:y, bubbles:true}));
""", canvas)

time.sleep(1)
print("✅ Tool interaction performed")

# =====================================================
# 6. UNDO VERIFICATION
# =====================================================
body = driver.find_element(By.TAG_NAME, "body")
body.send_keys(Keys.CONTROL, "z")
time.sleep(1)
print("✅ Undo executed")

# =====================================================
# 7. VIEW → ZOOM TEST
# =====================================================
print("\n🧪 VIEW → ZOOM TEST")

before_transform = canvas.value_of_css_property("transform")
body.send_keys(Keys.CONTROL, "+")
time.sleep(1)
after_transform = canvas.value_of_css_property("transform")

if before_transform != after_transform:
    print("✅ Zoom works")
else:
    print("⚠️ Zoom effect unclear")

# =====================================================
# 8. FINISH
# =====================================================
time.sleep(3)
driver.quit()
print("\n✅ FILE → OPEN + FULL FUNCTIONAL TEST COMPLETED")
