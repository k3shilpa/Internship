import time
import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# =====================================================
# CONFIG
# =====================================================
URL = "https://fixthephoto.com/online-gimp-editor.html"
IMAGE_PATH = r"D:\Internship\test.jpg"
REPORT_PATH = "gimp_exploratory_report.json"

if not os.path.exists(IMAGE_PATH):
    raise Exception("❌ Image not found")

# =====================================================
# SETUP
# =====================================================
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.maximize_window()
wait = WebDriverWait(driver, 40)

report = {
    "editor": "FixThePhoto Online GIMP",
    "image_loaded": False,
    "tools": []
}

# =====================================================
# STEP 1: OPEN EDITOR
# =====================================================
driver.get(URL)
print("✅ Editor opened")

# =====================================================
# STEP 2: SWITCH TO EDITOR IFRAME
# =====================================================
iframes = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "iframe")))
editor_iframe = None

for iframe in iframes:
    driver.switch_to.default_content()
    driver.switch_to.frame(iframe)
    try:
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "toolbtn")))
        editor_iframe = iframe
        print("✅ Editor iframe detected")
        break
    except:
        continue

if not editor_iframe:
    driver.quit()
    raise Exception("❌ Editor iframe not found")

# =====================================================
# STEP 3: UPLOAD IMAGE
# =====================================================
file_inputs = driver.find_elements(By.XPATH, "//input[@type='file']")
file_inputs[0].send_keys(IMAGE_PATH)
time.sleep(3)

report["image_loaded"] = True
print("🖼️ Image uploaded")

# =====================================================
# STEP 4: DETECT SIDEBAR TOOLS
# =====================================================
tools = driver.find_elements(By.CSS_SELECTOR, "button.toolbtn")
print(f"🔧 Total tools detected: {len(tools)}")

# =====================================================
# STEP 5: EXPLORE TOOLS (ACTIVATION ONLY)
# =====================================================
for index, tool in enumerate(tools):
    tool_info = {
        "index": index,
        "title": tool.get_attribute("title"),
        "activated": False,
        "activation_indicator": None
    }

    try:
        # Click tool
        tool.click()
        time.sleep(0.4)

        # Detect activation via class
        class_attr = tool.get_attribute("class") or ""
        aria_pressed = tool.get_attribute("aria-pressed")
        style = tool.value_of_css_property("background-color")

        if "active" in class_attr.lower():
            tool_info["activated"] = True
            tool_info["activation_indicator"] = "class=active"
        elif aria_pressed == "true":
            tool_info["activated"] = True
            tool_info["activation_indicator"] = "aria-pressed=true"
        else:
            tool_info["activation_indicator"] = f"css-bg={style}"

        print(
            f"➡ Tool {index:02d} | "
            f"{tool_info['title']} | "
            f"Activated={tool_info['activated']}"
        )

    except Exception as e:
        tool_info["error"] = str(e)
        print(f"⚠ Tool {index} failed")

    report["tools"].append(tool_info)

# =====================================================
# STEP 6: SAVE EXPLORATORY REPORT
# =====================================================
with open(REPORT_PATH, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

print(f"\n📄 Exploratory report saved to: {REPORT_PATH}")

# =====================================================
# FINISH
# =====================================================
input("\n✅ Exploratory testing complete. Press ENTER to exit...")
driver.quit()
