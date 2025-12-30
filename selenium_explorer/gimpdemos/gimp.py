import time
import pyautogui
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ---------------- SAFETY ----------------
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.2

# ---------------- SETUP ----------------
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.maximize_window()
wait = WebDriverWait(driver, 30)

driver.get("https://fixthephoto.com/online-gimp-editor.html")

# ---------------- WAIT FOR PAGE ----------------
wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

# ---------------- GET IFRAME POSITION (PARENT) ----------------
iframe = wait.until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))

iframe_pos = driver.execute_script("""
    const r = arguments[0].getBoundingClientRect();
    return { left: r.left, top: r.top };
""", iframe)

iframe_left = iframe_pos["left"]
iframe_top = iframe_pos["top"]

# ---------------- SWITCH INTO IFRAME ----------------
driver.switch_to.frame(iframe)
time.sleep(3)

topbar = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "topbar")))
print("✅ Editor ready")

# ---------------- GET TOPBAR MENU POSITIONS ----------------
menus = driver.execute_script("""
    const bar = arguments[0];
    const names = ["File","Edit","Image","Layer","Select","Filter","View","Window","More"];
    const result = [];

    names.forEach(name => {
        const el = Array.from(bar.querySelectorAll('*'))
            .find(e => e.innerText.trim() === name);
        if (el) {
            const r = el.getBoundingClientRect();
            result.push({
                name,
                x: r.left + r.width / 2,
                y: r.top + r.height / 2
            });
        }
    });

    return result;
""", topbar)

print(f"🔎 Found {len(menus)} topbar menus")

# ---------------- VISUAL EXPLORATION ----------------
for menu in menus:
    sx = iframe_left + menu["x"]
    sy = iframe_top + menu["y"]

    print(f"🧪 Opening {menu['name']}")

    pyautogui.moveTo(sx, sy, duration=0.3)
    pyautogui.click()

    time.sleep(2.5)   # MENU OPENS VISIBLY

    # move down slightly so options are visible
    pyautogui.moveTo(sx, sy + 200, duration=0.3)
    time.sleep(1)

    # close menu
    pyautogui.click()
    time.sleep(1)

print("🎉 TOPBAR EXPLORATION DONE")
driver.quit()
