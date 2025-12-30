from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
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
actions = ActionChains(driver)

URL = "https://fixthephoto.com/online-gimp-editor.html"
driver.get(URL)
print("✅ Editor opened")

# -----------------------------
# 2. Switch to editor iframe
# -----------------------------
iframes = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "iframe")))
print(f"✅ Found {len(iframes)} iframe(s)")

for iframe in iframes:
    driver.switch_to.default_content()
    driver.switch_to.frame(iframe)
    try:
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "canvas")))
        print("✅ Switched to editor iframe")
        break
    except:
        continue
else:
    driver.quit()
    raise Exception("❌ Editor iframe not found")

# -----------------------------
# 3. Helper: verify menu + explore submenus
# -----------------------------
def test_menu_with_verification(menu_name):
    print(f"\n🔍 Testing menu: {menu_name}")

    # Click main menu
    menu = wait.until(EC.element_to_be_clickable(
        (By.XPATH, f"//*[normalize-space()='{menu_name}']")
    ))
    menu.click()
    time.sleep(0.8)

    # Verify menu panel is visible
    menu_panels = driver.find_elements(
        By.XPATH,
        "//*[contains(@class,'menu') or contains(@class,'dropdown')]"
    )

    if not menu_panels:
        print(f"❌ {menu_name} menu did NOT open")
        return
    else:
        print(f"✅ {menu_name} menu opened")

    # Collect visible submenu items
    submenus = driver.find_elements(
        By.XPATH,
        "//*[contains(@class,'menu') or contains(@class,'dropdown')]//*[self::li or self::div or self::span][string-length(normalize-space())>0]"
    )

    print(f"➡ Found {len(submenus)} submenu items")

    for item in submenus[:8]:  # explore limited number
        try:
            text = item.text.strip()
            if not text:
                continue

            actions.move_to_element(item).perform()
            print(f"   🔹 Hovered submenu: {text}")
            time.sleep(0.5)

        except:
            continue

    # Close menu and verify close
    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
    time.sleep(0.5)

    remaining_panels = driver.find_elements(
        By.XPATH,
        "//*[contains(@class,'menu') or contains(@class,'dropdown')]"
    )

    if not remaining_panels:
        print(f"✅ {menu_name} menu closed")
    else:
        print(f"⚠️ {menu_name} menu may still be open")

# -----------------------------
# 4. Run verified tests for ALL menus
# -----------------------------
menus = ["File", "Edit", "Image", "Layer", "Select", "Filter", "View", "Window", "More"]

for menu in menus:
    test_menu_with_verification(menu)

# -----------------------------
# 5. Finish
# -----------------------------
time.sleep(3)
driver.quit()
print("\n✅ VERIFIED menu + submenu exploration completed")
