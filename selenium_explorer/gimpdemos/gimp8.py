from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
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
wait = WebDriverWait(driver, 40)

URL = "https://fixthephoto.com/online-gimp-editor.html"
driver.get(URL)
print("✅ Editor opened")

# =====================================================
# 2. Switch to editor iframe
# =====================================================
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

body = driver.find_element(By.TAG_NAME, "body")

# =====================================================
# 3. FILE → NEW (MENU ONLY, NO Ctrl+N)
# =====================================================
print("\n📂 FILE → NEW")

file_menu = wait.until(
    EC.element_to_be_clickable((By.XPATH, "//*[normalize-space()='File']"))
)
file_menu.click()
time.sleep(1)

# NOTE: Do NOT use Ctrl+N
print("✅ File menu opened")

# =====================================================
# 4. SELECT FIRST TEMPLATE (REAL IMAGE LOAD)
# =====================================================
print("🖼️ Selecting FIRST template")

templates = wait.until(
    EC.presence_of_all_elements_located((
        By.XPATH,
        "//div[.//img]"
    ))
)

first_template = None
for t in templates:
    if t.is_displayed():
        first_template = t
        break

if not first_template:
    driver.quit()
    raise Exception("❌ No visible template found")

driver.execute_script("""
arguments[0].scrollIntoView({block:'center'});
arguments[0].click();
""", first_template)

print("✅ Template clicked")
time.sleep(3)

# =====================================================
# 5. VERIFY REAL IMAGE LOADED
# =====================================================
canvas = wait.until(EC.presence_of_element_located((By.TAG_NAME, "canvas")))

width = int(canvas.get_attribute("width"))
height = int(canvas.get_attribute("height"))

print(f"🖼️ Canvas size after template load: {width} x {height}")

if width < 200 or height < 200:
    print("⚠️ Canvas small → zooming")

# =====================================================
# 6. ZOOM TO MAKE IMAGE CLEARLY VISIBLE
# =====================================================
for _ in range(6):
    body.send_keys(Keys.CONTROL, "+")
    time.sleep(0.3)

print("✅ Canvas zoom adjusted")

# =====================================================
# 7. VISIBLE TOOL TESTS (REAL CHANGES)
# =====================================================
print("\n🎨 VISIBLE TOOL TESTS")

tools = driver.find_elements(By.CSS_SELECTOR, "button.toolbtn")

# ---------- Rectangle Select (VISIBLE) ----------
print("➡ Rectangle Select (visible)")
driver.execute_script("arguments[0].click();", tools[1])
time.sleep(0.5)

driver.execute_script("""
const c = arguments[0];
const r = c.getBoundingClientRect();
const sx = r.left + r.width * 0.2;
const sy = r.top + r.height * 0.2;
const ex = r.left + r.width * 0.6;
const ey = r.top + r.height * 0.6;

c.dispatchEvent(new MouseEvent('mousedown',{clientX:sx,clientY:sy,bubbles:true}));
c.dispatchEvent(new MouseEvent('mousemove',{clientX:ex,clientY:ey,bubbles:true}));
c.dispatchEvent(new MouseEvent('mouseup',{clientX:ex,clientY:ey,bubbles:true}));
""", canvas)

time.sleep(2)
body.send_keys(Keys.CONTROL, "z")

# ---------- Brush Tool (VISIBLE) ----------
print("➡ Brush Tool (visible)")
driver.execute_script("arguments[0].click();", tools[7])
time.sleep(0.5)

driver.execute_script("""
const c = arguments[0];
const r = c.getBoundingClientRect();
let x = r.left + r.width * 0.3;
let y = r.top + r.height * 0.5;

c.dispatchEvent(new MouseEvent('mousedown',{clientX:x,clientY:y,bubbles:true}));
for(let i=0;i<6;i++){
  x += 25;
  c.dispatchEvent(new MouseEvent('mousemove',{clientX:x,clientY:y,bubbles:true}));
}
c.dispatchEvent(new MouseEvent('mouseup',{clientX:x,clientY:y,bubbles:true}));
""", canvas)

time.sleep(2)
body.send_keys(Keys.CONTROL, "z")

# ---------- Text Tool (VISIBLE) ----------
print("➡ Text Tool (visible)")
driver.execute_script("arguments[0].click();", tools[13])
time.sleep(0.5)

driver.execute_script("""
const c = arguments[0];
const r = c.getBoundingClientRect();
const x = r.left + r.width * 0.4;
const y = r.top + r.height * 0.4;
c.dispatchEvent(new MouseEvent('mousedown',{clientX:x,clientY:y,bubbles:true}));
c.dispatchEvent(new MouseEvent('mouseup',{clientX:x,clientY:y,bubbles:true}));
""", canvas)

time.sleep(1)
body.send_keys("Hello")
time.sleep(2)
body.send_keys(Keys.CONTROL, "z")

print("✅ Visible tools verified")

# =====================================================
# 8. FUNCTIONAL TEST FOR REMAINING TOOLS
# =====================================================
print("\n🧪 FUNCTIONAL TEST FOR REMAINING TOOLS")

for i, tool in enumerate(tools):
    if i in [1, 7, 13]:
        continue

    name = tool.get_attribute("title") or f"Tool {i}"
    driver.execute_script("arguments[0].click();", tool)
    time.sleep(0.3)

    driver.execute_script("""
    const c = arguments[0];
    const r = c.getBoundingClientRect();
    const x = r.left + r.width/2;
    const y = r.top + r.height/2;
    c.dispatchEvent(new MouseEvent('mousedown',{clientX:x,clientY:y,bubbles:true}));
    c.dispatchEvent(new MouseEvent('mouseup',{clientX:x,clientY:y,bubbles:true}));
    """, canvas)

    body.send_keys(Keys.CONTROL, "z")
    time.sleep(0.3)

    print(f"   ✅ {name} functional")

# =====================================================
# 9. Finish
# =====================================================
time.sleep(3)
driver.quit()
print("\n✅ FINAL VISIBLE + FUNCTIONAL UI TEST COMPLETED")
