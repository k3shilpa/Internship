from selenium import webdriver
from selenium.webdriver.common.by import By
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
wait = WebDriverWait(driver, 30)

URL = "https://fixthephoto.com/online-gimp-editor.html"
driver.get(URL)
print("✅ Editor opened")

# -----------------------------
# 2. Switch to editor iframe
# -----------------------------
iframes = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "iframe")))

for iframe in iframes:
    driver.switch_to.default_content()
    driver.switch_to.frame(iframe)
    try:
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "toolbtn")))
        print("✅ Switched to editor iframe")
        break
    except:
        continue
else:
    driver.quit()
    raise Exception("❌ Editor iframe not found")

# -----------------------------
# 3. Get all toolbar tools
# -----------------------------
tools = wait.until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "button.toolbtn"))
)

print(f"\n🧰 Found {len(tools)} tools\n")

# -----------------------------
# 4. Click tool and VERIFY ACTIVE
# -----------------------------
for tool in tools:
    tool_name = tool.get_attribute("title") or "Unnamed Tool"

    # Click tool
    tool.click()
    time.sleep(0.6)  # allow UI state update

    # Re-fetch tool (DOM may update class)
    refreshed_tools = driver.find_elements(By.CSS_SELECTOR, "button.toolbtn")

    active_tools = [
        t for t in refreshed_tools
        if "active" in (t.get_attribute("class") or "")
    ]

    print(f"➡ Clicked: {tool_name}")

    # -------- VERIFICATION --------
    if len(active_tools) != 1:
        print(f"   ❌ ERROR: {len(active_tools)} active tools found (expected 1)")
        continue

    active_tool = active_tools[0]
    active_name = active_tool.get_attribute("title")

    if active_name == tool_name:
        print(f"   ✅ PASS: '{tool_name}' is ACTIVE")
    else:
        print(f"   ❌ FAIL: '{tool_name}' not active, '{active_name}' is active")

# -----------------------------
# 5. Finish
# -----------------------------
time.sleep(3)
driver.quit()
print("\n✅ Tool active-state verification completed")
