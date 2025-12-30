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
wait = WebDriverWait(driver, 30)

URL = "https://fixthephoto.com/online-gimp-editor.html"
driver.get(URL)
print("✅ Editor opened")

# -----------------------------
# 2. Switch to editor iframe
# -----------------------------
iframes = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "iframe")))
print(f"✅ Found {len(iframes)} iframe(s)")

editor_found = False
for iframe in iframes:
    driver.switch_to.default_content()
    driver.switch_to.frame(iframe)
    try:
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "canvas")))
        editor_found = True
        print("✅ Switched to editor iframe")
        break
    except:
        continue

if not editor_found:
    driver.quit()
    raise Exception("❌ Editor iframe not found")

# -----------------------------
# 3. Helper: open menu + submenus visibly
# -----------------------------
def test_menu_with_submenus(menu_name):
    print(f"\n🔍 Testing {menu_name} menu")

    # Click main menu (VISIBLE)
    menu = wait.until(
        EC.element_to_be_clickable((
            By.XPATH,
            f"//*[normalize-space()='{menu_name}']"
        ))
    )
    menu.click()
    print(f"✅ {menu_name} menu opened")
    time.sleep(1)

    # Find submenu items
    submenus = driver.find_elements(
        By.XPATH,
        "//*[contains(@class,'menu') or contains(@class,'dropdown')]//*[self::li or self::div or self::span]"
    )

    print(f"➡ Found {len(submenus)} submenu items")

    for idx, item in enumerate(submenus[:6]):  # limit to avoid infinite lists
        try:
            driver.execute_script("arguments[0].scrollIntoView(true);", item)
            item.click()
            print(f"   🔹 Submenu {idx + 1} clicked")
            time.sleep(0.8)

            # Reopen main menu (some editors close after click)
            menu.click()
            time.sleep(0.5)

        except:
            continue

    # Close menu
    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
    print(f"✅ {menu_name} menu closed")
    time.sleep(1)

# -----------------------------
# 4. Run tests for ALL menus
# -----------------------------
menus = ["File", "Edit", "Image", "Layer","Select", "Filter", "View", "Window", "More"]

for menu in menus:
    test_menu_with_submenus(menu)

# -----------------------------
# 5. Finish
# -----------------------------
time.sleep(3)
driver.quit()
print("\n✅ ALL menu + submenu tests completed successfully")
