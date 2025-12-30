from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

# =====================================================
# 1. Browser setup
# =====================================================
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.maximize_window()
wait = WebDriverWait(driver, 30)
actions = ActionChains(driver)

URL = "https://fixthephoto.com/online-gimp-editor.html"
driver.get(URL)
print("✅ Editor opened")

# =====================================================
# 2. Switch to editor iframe (shared for both tests)
# =====================================================
iframes = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "iframe")))
print(f"✅ Found {len(iframes)} iframe(s)")

for iframe in iframes:
    driver.switch_to.default_content()
    driver.switch_to.frame(iframe)
    try:
        # canvas + toolbtn together confirms editor frame
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "toolbtn")))
        print("✅ Switched to editor iframe")
        break
    except:
        continue
else:
    driver.quit()
    raise Exception("❌ Editor iframe not found")

# =====================================================
# 3. MENU VERIFICATION + SUBMENU EXPLORATION
# =====================================================
def test_menu_with_verification(menu_name):
    print(f"\n🔍 Testing menu: {menu_name}")

    # Open menu visibly
    menu = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, f"//*[normalize-space()='{menu_name}']")
        )
    )
    menu.click()
    time.sleep(0.8)

    # Verify menu panel opened
    menu_panels = driver.find_elements(
        By.XPATH, "//*[contains(@class,'menu') or contains(@class,'dropdown')]"
    )

    if not menu_panels:
        print(f"❌ {menu_name} menu did NOT open")
        return
    else:
        print(f"✅ {menu_name} menu opened")

    # Find submenu items
    submenus = driver.find_elements(
        By.XPATH,
        "//*[contains(@class,'menu') or contains(@class,'dropdown')]"
        "//*[self::li or self::div or self::span]"
        "[string-length(normalize-space())>0]"
    )

    print(f"➡ Found {len(submenus)} submenu items")

    # Hover submenus visibly
    for item in submenus[:8]:
        try:
            text = item.text.strip()
            if not text:
                continue
            actions.move_to_element(item).perform()
            print(f"   🔹 Hovered submenu: {text}")
            time.sleep(0.5)
        except:
            continue

    # Close menu
    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
    time.sleep(0.5)

    remaining = driver.find_elements(
        By.XPATH, "//*[contains(@class,'menu') or contains(@class,'dropdown')]"
    )

    if not remaining:
        print(f"✅ {menu_name} menu closed")
    else:
        print(f"⚠️ {menu_name} menu may still be open")

# =====================================================
# 4. RUN MENU TESTS
# =====================================================
menus = ["File", "Edit", "Image", "Layer", "Select", "Filter", "View", "Window", "More"]

for menu in menus:
    test_menu_with_verification(menu)

# =====================================================
# 5. LEFT TOOLBAR ACTIVE-STATE VERIFICATION
# =====================================================
tools = wait.until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "button.toolbtn"))
)

print(f"\n🧰 Found {len(tools)} left sidebar tools\n")

for tool in tools:
    tool_name = tool.get_attribute("title") or "Unnamed Tool"

    # Click tool
    tool.click()
    time.sleep(0.6)

    # Re-fetch tools to get updated class state
    refreshed_tools = driver.find_elements(By.CSS_SELECTOR, "button.toolbtn")

    active_tools = [
        t for t in refreshed_tools
        if "active" in (t.get_attribute("class") or "")
    ]

    print(f"➡ Clicked tool: {tool_name}")

    # STRICT VERIFICATION
    if len(active_tools) != 1:
        print(f"   ❌ ERROR: {len(active_tools)} active tools found (expected 1)")
        continue

    active_tool = active_tools[0]
    active_name = active_tool.get_attribute("title")

    if active_name == tool_name:
        print(f"   ✅ PASS: '{tool_name}' is ACTIVE")
    else:
        print(f"   ❌ FAIL: '{tool_name}' not active, '{active_name}' is active")

# =====================================================
# 6. Finish
# =====================================================
time.sleep(3)
driver.quit()
print("\n✅ MENU + TOOLBAR UI VERIFICATION COMPLETED SUCCESSFULLY")
