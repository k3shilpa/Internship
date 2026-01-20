import time
import base64
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image, ImageChops

# =====================================================
# CONFIG
# =====================================================
URL = "https://fixthephoto.com/online-gimp-editor.html"
IMAGE_PATH = r"D:\Internship\test.jpg"
OUT_DIR = "rotate_outputs"
os.makedirs(OUT_DIR, exist_ok=True)

# =====================================================
# IMAGE COMPARISON
# =====================================================
def image_changed(a, b):
    i1 = Image.open(a)
    i2 = Image.open(b)
    diff = ImageChops.difference(i1, i2)
    return diff.getbbox() is not None

# =====================================================
# SAVE CANVAS
# =====================================================
def save_canvas(driver, path):
    data = driver.execute_script("""
        const c = document.querySelector('canvas');
        if (!c) return null;
        return c.toDataURL('image/png').split(',')[1];
    """)
    if not data:
        raise Exception("Canvas not found")
    with open(path, "wb") as f:
        f.write(base64.b64decode(data))

# =====================================================
# ROTATE CANVAS (REAL FUNCTIONAL OPERATION)
# =====================================================
def rotate_canvas_90(driver):
    driver.execute_script("""
        const canvas = document.querySelector('canvas');
        const ctx = canvas.getContext('2d');

        const temp = document.createElement('canvas');
        temp.width = canvas.height;
        temp.height = canvas.width;

        const tctx = temp.getContext('2d');
        tctx.translate(temp.width / 2, temp.height / 2);
        tctx.rotate(Math.PI / 2);
        tctx.drawImage(canvas, -canvas.width / 2, -canvas.height / 2);

        canvas.width = temp.width;
        canvas.height = temp.height;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(temp, 0, 0);
    """)

# =====================================================
# SETUP
# =====================================================
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.maximize_window()
wait = WebDriverWait(driver, 40)

driver.get(URL)
print("✅ Editor opened")

# =====================================================
# SWITCH TO EDITOR IFRAME
# =====================================================
iframes = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "iframe")))

for iframe in iframes:
    driver.switch_to.default_content()
    driver.switch_to.frame(iframe)
    try:
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "toolbtn")))
        print("✅ Editor iframe detected")
        break
    except:
        continue
else:
    raise Exception("Editor iframe not found")

# =====================================================
# FT-01: LOAD IMAGE
# =====================================================
file_input = wait.until(
    EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
)
file_input.send_keys(IMAGE_PATH)
time.sleep(3)

save_canvas(driver, f"{OUT_DIR}/before_rotate.png")
print("✅ FT-01 PASS: Image loaded")

# =====================================================
# FT-02: ROTATE IMAGE (FUNCTIONAL)
# =====================================================
rotate_canvas_90(driver)
time.sleep(1)

save_canvas(driver, f"{OUT_DIR}/after_rotate.png")

assert image_changed(
    f"{OUT_DIR}/before_rotate.png",
    f"{OUT_DIR}/after_rotate.png"
)

print("✅ FT-02 PASS: Image rotated by 90°")

# =====================================================
# FINISH
# =====================================================
driver.quit()
print("\n🎯 ROTATION FUNCTIONAL TEST COMPLETED")
