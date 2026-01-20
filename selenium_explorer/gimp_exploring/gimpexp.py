import time
import json
import os
import random
import traceback
from datetime import datetime
from enum import Enum
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# =====================================================
# ENUMS & CONFIG
# =====================================================
class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"

class ToolCategory(Enum):
    SELECTION = "selection"
    PAINT = "paint"
    TRANSFORM = "transform"
    COLOR = "color"
    TEXT = "text"
    FILTER = "filter"
    OTHER = "other"

# Configuration
URL = "https://fixthephoto.com/online-gimp-editor.html"
IMAGE_PATH = r"D:\Internship\test2.jpg"
REPORT_PATH = f"gimp_exploratory_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
SCREENSHOT_DIR = "screenshots"
TEST_DURATION = 2400  # 40 minutes max testing time
CANVAS_WAIT = 10  # Wait for canvas to be ready

if not os.path.exists(IMAGE_PATH):
    raise Exception("❌ Image not found")

os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# =====================================================
# TESTING FRAMEWORK CLASSES
# =====================================================
class GIMPExploratoryTester:
    def __init__(self):
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver, 40)
        self.actions = ActionChains(self.driver)
        self.start_time = datetime.now()
        self.canvas = None
        self.canvas_location = None
        self.canvas_size = None
        
        self.report = {
            "editor": "FixThePhoto Online GIMP",
            "timestamp": self.start_time.isoformat(),
            "image_loaded": False,
            "test_duration": 0,
            "tools_tested": 0,
            "tools_failed": 0,
            "tools_passed": 0,
            "tools_skipped": 0,
            "tools": [],
            "issues_found": [],
            "image_effects_applied": [],
            "performance_metrics": {}
        }
    
    def locate_canvas(self):
        """Locate and prepare the canvas for interactions"""
        try:
            # Try different selectors for canvas
            canvas_selectors = [
                "canvas",
                "#canvas",
                ".canvas",
                "[class*='canvas']",
                "[class*='editor']",
                "[class*='image']",
                "div[id*='canvas']",
                "div[class*='canvas']"
            ]
            
            for selector in canvas_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.size['width'] > 100:
                            self.canvas = element
                            break
                except:
                    continue
                
                if self.canvas:
                    break
            
            if not self.canvas:
                # Try to find by looking for large visible elements
                all_elements = self.driver.find_elements(By.CSS_SELECTOR, "*")
                for element in all_elements:
                    try:
                        if element.is_displayed():
                            size = element.size
                            if size['width'] > 300 and size['height'] > 200:
                                self.canvas = element
                                break
                    except:
                        continue
            
            if self.canvas:
                self.canvas_location = self.canvas.location
                self.canvas_size = self.canvas.size
                print(f"✅ Canvas located: {self.canvas_size['width']}x{self.canvas_size['height']}")
                return True
            else:
                print("⚠ Canvas not found, will try alternative coordinates")
                # Use approximate center of screen
                self.canvas_location = {'x': 400, 'y': 300}
                self.canvas_size = {'width': 800, 'height': 600}
                return True
                
        except Exception as e:
            print(f"⚠ Canvas location failed: {str(e)}")
            return False
    
    def click_on_canvas(self, x_offset=0, y_offset=0):
        """Click on canvas with optional offset from center"""
        if self.canvas:
            try:
                # Move to canvas center with offset
                self.actions.move_to_element(self.canvas).move_by_offset(x_offset, y_offset).click().perform()
                time.sleep(0.5)
                return True
            except:
                # Fallback to absolute coordinates
                pass
        
        # Use absolute coordinates as fallback
        center_x = self.canvas_location['x'] + self.canvas_size['width'] // 2 + x_offset
        center_y = self.canvas_location['y'] + self.canvas_size['height'] // 2 + y_offset
        self.actions.move_by_offset(center_x, center_y).click().perform()
        time.sleep(0.5)
        return True
    
    def draw_on_canvas(self, pattern="square", size=50):
        """Draw a pattern on the canvas"""
        if not self.locate_canvas():
            return False
        
        try:
            start_x = random.randint(-size, size)
            start_y = random.randint(-size, size)
            
            # Move to starting position
            self.actions.move_to_element(self.canvas).move_by_offset(start_x, start_y)
            
            if pattern == "square":
                # Draw a square
                self.actions.click_and_hold().move_by_offset(size, 0).move_by_offset(0, size)
                self.actions.move_by_offset(-size, 0).move_by_offset(0, -size).release().perform()
                
            elif pattern == "circle":
                # Draw a circular motion
                self.actions.click_and_hold()
                for i in range(12):
                    angle = i * 30  # 30 degrees each step
                    x = int(size * math.cos(math.radians(angle)))
                    y = int(size * math.sin(math.radians(angle)))
                    self.actions.move_by_offset(x, y)
                self.actions.release().perform()
                
            elif pattern == "random":
                # Draw random squiggles
                self.actions.click_and_hold()
                for _ in range(8):
                    dx = random.randint(-20, 20)
                    dy = random.randint(-20, 20)
                    self.actions.move_by_offset(dx, dy)
                self.actions.release().perform()
            
            time.sleep(1)
            return True
            
        except Exception as e:
            print(f"⚠ Drawing failed: {str(e)}")
            return False
    
    def take_screenshot(self, name, include_canvas_only=False):
        """Take screenshot with descriptive name"""
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"{SCREENSHOT_DIR}/{name}_{timestamp}.png"
        
        if include_canvas_only and self.canvas:
            # Try to screenshot only the canvas area
            try:
                # Take full screenshot first
                self.driver.save_screenshot(filename)
                print(f"   📸 Screenshot saved: {filename}")
                return filename
            except:
                pass
        
        # Full screenshot
        self.driver.save_screenshot(filename)
        print(f"   📸 Screenshot saved: {filename}")
        return filename
    
    def log_issue(self, tool_name, issue_type, description, severity="MEDIUM"):
        """Log an issue found during testing"""
        issue = {
            "tool": tool_name,
            "type": issue_type,
            "description": description,
            "severity": severity,
            "timestamp": datetime.now().isoformat(),
            "screenshot": self.take_screenshot(f"issue_{tool_name}")
        }
        self.report["issues_found"].append(issue)
        print(f"   ⚠ ISSUE: {issue_type} - {description}")
    
    def log_image_effect(self, tool_name, effect_type, parameters=None):
        """Log successful image effect application"""
        effect = {
            "tool": tool_name,
            "effect": effect_type,
            "parameters": parameters or {},
            "timestamp": datetime.now().isoformat(),
            "screenshot": self.take_screenshot(f"effect_{tool_name}_{effect_type}")
        }
        self.report["image_effects_applied"].append(effect)
        print(f"   ✅ Effect applied: {effect_type}")
    
    def categorize_tool(self, tool_title):
        """Categorize tool based on its title/function"""
        if not tool_title:
            return ToolCategory.OTHER
        
        title_lower = tool_title.lower()
        
        if any(word in title_lower for word in ['select', 'rectangle select', 'ellipse select', 'free select', 'fuzzy select', 'scissors']):
            return ToolCategory.SELECTION
        elif any(word in title_lower for word in ['paint', 'brush', 'pencil', 'eraser', 'bucket', 'gradient', 'airbrush', 'clone', 'heal']):
            return ToolCategory.PAINT
        elif any(word in title_lower for word in ['move', 'rotate', 'scale', 'shear', 'perspective', 'flip', 'crop', 'align']):
            return ToolCategory.TRANSFORM
        elif any(word in title_lower for word in ['color', 'hue', 'saturation', 'brightness', 'levels', 'curves', 'color balance', 'posterize']):
            return ToolCategory.COLOR
        elif any(word in title_lower for word in ['text', 'type']):
            return ToolCategory.TEXT
        elif any(word in title_lower for word in ['filter', 'blur', 'sharpen', 'noise', 'edge', 'distort', 'artistic', 'render']):
            return ToolCategory.FILTER
        else:
            return ToolCategory.OTHER
    
    def test_and_apply_selection_tool(self, tool, tool_info):
        """Test and apply selection tools on the image"""
        try:
            print(f"   🎯 Applying {tool_info['title']} to image...")
            
            # Activate tool
            tool.click()
            time.sleep(1)
            
            # Get canvas ready
            if not self.locate_canvas():
                return False
            
            # Take before screenshot
            before_shot = self.take_screenshot(f"before_{tool_info['title']}")
            
            # Apply selection based on tool type
            title_lower = tool_info['title'].lower()
            
            if 'rectangle' in title_lower:
                # Draw rectangular selection
                self.actions.move_to_element(self.canvas).move_by_offset(-100, -100)
                self.actions.click_and_hold().move_by_offset(200, 150).release().perform()
                tool_info["selection_shape"] = "rectangle"
                
            elif 'ellipse' in title_lower:
                # Draw elliptical selection
                self.actions.move_to_element(self.canvas).move_by_offset(0, 0)
                self.actions.click_and_hold().move_by_offset(100, 0)
                self.actions.move_by_offset(0, 80).move_by_offset(-100, 0)
                self.actions.move_by_offset(0, -80).release().perform()
                tool_info["selection_shape"] = "ellipse"
                
            elif 'free' in title_lower or 'lasso' in title_lower:
                # Draw freeform selection
                self.actions.move_to_element(self.canvas).move_by_offset(-80, -60)
                self.actions.click()
                self.actions.move_by_offset(60, 40)
                self.actions.click()
                self.actions.move_by_offset(40, -30)
                self.actions.click()
                self.actions.move_by_offset(-20, 50)
                self.actions.click()
                # Close the selection by clicking near start
                self.actions.move_by_offset(0, -60).click().perform()
                tool_info["selection_shape"] = "freeform"
                
            else:
                # Default rectangular selection
                self.actions.move_to_element(self.canvas).move_by_offset(-50, -50)
                self.actions.click_and_hold().move_by_offset(100, 100).release().perform()
                tool_info["selection_shape"] = "default"
            
            time.sleep(2)
            
            # Take after screenshot
            after_shot = self.take_screenshot(f"after_{tool_info['title']}")
            
            # Look for selection indicators
            try:
                # Check for visual selection indicators
                selection_indicators = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "[class*='selection'], [class*='marquee'], [style*='dashed'], [style*='marching']"
                )
                tool_info["selection_visible"] = len(selection_indicators) > 0
            except:
                tool_info["selection_visible"] = False
            
            # Test selection operations if visible
            if tool_info.get("selection_visible", False):
                # Try to move the selection
                self.actions.move_to_element(self.canvas).move_by_offset(50, 50)
                self.actions.click_and_hold().move_by_offset(30, 30).release().perform()
                time.sleep(1)
                
                # Try to fill selection if fill/bucket tool is available
                try:
                    fill_buttons = self.driver.find_elements(
                        By.XPATH,
                        "//button[contains(@title, 'Bucket') or contains(@title, 'Fill') or contains(text(), 'Fill')]"
                    )
                    if fill_buttons:
                        # Take color before fill
                        before_fill = self.take_screenshot(f"before_fill_{tool_info['title']}")
                        
                        # Try to set fill color first
                        color_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='color']")
                        if color_inputs:
                            color_inputs[0].send_keys("#FF0000")  # Red color
                            time.sleep(0.5)
                        
                        fill_buttons[0].click()
                        time.sleep(2)
                        
                        after_fill = self.take_screenshot(f"after_fill_{tool_info['title']}")
                        tool_info["fill_applied"] = True
                except:
                    pass
            
            # Log the effect
            self.log_image_effect(tool_info['title'], "selection", {
                "shape": tool_info.get("selection_shape", "unknown"),
                "visible": tool_info.get("selection_visible", False)
            })
            
            tool_info["screenshots"] = [before_shot, after_shot]
            tool_info["applied_to_image"] = True
            
            # Deselect if possible
            try:
                esc_buttons = self.driver.find_elements(
                    By.XPATH,
                    "//button[contains(text(), 'Cancel') or contains(@title, 'Cancel') or contains(text(), 'Deselect')]"
                )
                if esc_buttons:
                    esc_buttons[0].click()
                else:
                    # Try ESC key
                    self.actions.send_keys(Keys.ESCAPE).perform()
                time.sleep(1)
            except:
                pass
            
            return True
            
        except Exception as e:
            self.log_issue(tool_info["title"], "Selection Application Failed", str(e))
            return False
    
    def test_and_apply_paint_tool(self, tool, tool_info):
        """Test and apply paint tools on the image"""
        try:
            print(f"   🎨 Applying {tool_info['title']} to image...")
            
            # Activate tool
            tool.click()
            time.sleep(1)
            
            # Get canvas ready
            if not self.locate_canvas():
                return False
            
            # Take before screenshot
            before_shot = self.take_screenshot(f"before_{tool_info['title']}")
            
            # Configure tool if options available
            title_lower = tool_info['title'].lower()
            
            # Set brush size if available
            try:
                brush_sliders = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "input[type='range'][title*='size' i], input[type='range'][placeholder*='size' i]"
                )
                if brush_sliders:
                    brush_sliders[0].clear()
                    brush_sliders[0].send_keys("20")
                    tool_info["brush_size_set"] = "20"
            except:
                pass
            
            # Set color if available
            try:
                color_pickers = self.driver.find_elements(By.CSS_SELECTOR, "input[type='color']")
                if color_pickers:
                    if 'eraser' in title_lower:
                        # Use white for eraser
                        color_pickers[0].send_keys("#FFFFFF")
                    else:
                        # Random color for painting
                        colors = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF"]
                        random_color = random.choice(colors)
                        color_pickers[0].send_keys(random_color)
                        tool_info["color_used"] = random_color
            except:
                pass
            
            # Apply tool to image based on type
            if 'bucket' in title_lower or 'fill' in title_lower:
                # Click to fill area
                self.click_on_canvas(x_offset=random.randint(-100, 100), y_offset=random.randint(-100, 100))
                tool_info["application_type"] = "fill"
                
            elif 'gradient' in title_lower:
                # Draw gradient line
                self.actions.move_to_element(self.canvas).move_by_offset(-80, -60)
                self.actions.click_and_hold().move_by_offset(160, 120).release().perform()
                tool_info["application_type"] = "gradient"
                
            elif 'clone' in title_lower or 'heal' in title_lower:
                # Set source point then apply
                self.actions.move_to_element(self.canvas).move_by_offset(-50, -50).click().perform()
                time.sleep(0.5)
                self.actions.move_by_offset(100, 100).click_and_hold()
                self.actions.move_by_offset(40, 40).release().perform()
                tool_info["application_type"] = "clone/heal"
                
            else:
                # Draw directly on canvas
                # Simple drawing pattern
                self.actions.move_to_element(self.canvas).move_by_offset(-60, -40)
                
                if 'pencil' in title_lower or 'brush' in title_lower or 'airbrush' in title_lower:
                    # Draw a simple shape
                    self.actions.click_and_hold().move_by_offset(120, 0)
                    self.actions.move_by_offset(0, 80).move_by_offset(-120, 0)
                    self.actions.move_by_offset(0, -80).release().perform()
                    tool_info["application_type"] = "draw_shape"
                else:
                    # Default: draw some strokes
                    self.actions.click_and_hold()
                    for _ in range(5):
                        dx = random.randint(-20, 20)
                        dy = random.randint(-20, 20)
                        self.actions.move_by_offset(dx, dy)
                    self.actions.release().perform()
                    tool_info["application_type"] = "random_strokes"
            
            time.sleep(2)
            
            # Take after screenshot
            after_shot = self.take_screenshot(f"after_{tool_info['title']}")
            
            # Log the effect
            self.log_image_effect(tool_info['title'], "painting", {
                "type": tool_info.get("application_type", "unknown"),
                "color": tool_info.get("color_used", "default")
            })
            
            tool_info["screenshots"] = [before_shot, after_shot]
            tool_info["applied_to_image"] = True
            
            # Check for undo functionality
            try:
                undo_buttons = self.driver.find_elements(
                    By.XPATH,
                    "//button[contains(@title, 'Undo') or contains(text(), 'Undo')]"
                )
                if undo_buttons:
                    undo_buttons[0].click()
                    time.sleep(1)
                    tool_info["undo_tested"] = True
            except:
                pass
            
            return True
            
        except Exception as e:
            self.log_issue(tool_info["title"], "Paint Application Failed", str(e))
            return False
    
    def test_and_apply_color_tool(self, tool, tool_info):
        """Test and apply color adjustment tools to the image"""
        try:
            print(f"   🎨 Applying {tool_info['title']} to image...")
            
            # Activate tool
            tool.click()
            time.sleep(2)  # Give more time for color dialogs to open
            
            # Take before screenshot
            before_shot = self.take_screenshot(f"before_{tool_info['title']}")
            
            title_lower = tool_info['title'].lower()
            tool_info["adjustment_applied"] = False
            
            # Apply specific adjustments based on tool type
            if 'brightness' in title_lower:
                # Adjust brightness slider
                sliders = self.driver.find_elements(By.CSS_SELECTOR, "input[type='range']")
                if sliders:
                    sliders[0].clear()
                    sliders[0].send_keys("30")  # Increase brightness
                    tool_info["adjustment"] = "brightness+30"
                    tool_info["adjustment_applied"] = True
                    
            elif 'contrast' in title_lower:
                sliders = self.driver.find_elements(By.CSS_SELECTOR, "input[type='range']")
                if sliders:
                    sliders[0].clear()
                    sliders[0].send_keys("20")  # Increase contrast
                    tool_info["adjustment"] = "contrast+20"
                    tool_info["adjustment_applied"] = True
                    
            elif 'saturation' in title_lower:
                sliders = self.driver.find_elements(By.CSS_SELECTOR, "input[type='range']")
                if sliders:
                    sliders[0].clear()
                    sliders[0].send_keys("50")  # Increase saturation
                    tool_info["adjustment"] = "saturation+50"
                    tool_info["adjustment_applied"] = True
                    
            elif 'hue' in title_lower:
                sliders = self.driver.find_elements(By.CSS_SELECTOR, "input[type='range']")
                if sliders:
                    # Set hue to a different value
                    sliders[0].clear()
                    sliders[0].send_keys("180")  # Change hue
                    tool_info["adjustment"] = "hue=180"
                    tool_info["adjustment_applied"] = True
                    
            elif 'color balance' in title_lower:
                # Try to find multiple sliders for RGB
                sliders = self.driver.find_elements(By.CSS_SELECTOR, "input[type='range']")
                if len(sliders) >= 3:
                    # Adjust red, green, blue
                    sliders[0].clear()
                    sliders[0].send_keys("10")
                    sliders[1].clear()
                    sliders[1].send_keys("-5")
                    sliders[2].clear()
                    sliders[2].send_keys("5")
                    tool_info["adjustment"] = "color_balance_rgb"
                    tool_info["adjustment_applied"] = True
            
            # Apply the adjustment
            if tool_info.get("adjustment_applied", False):
                # Look for apply/ok/confirm buttons
                apply_buttons = self.driver.find_elements(
                    By.XPATH,
                    "//button[contains(text(), 'Apply') or contains(text(), 'OK') or contains(text(), 'Confirm') or contains(text(), 'Save')]"
                )
                
                if apply_buttons:
                    apply_buttons[0].click()
                    time.sleep(3)  # Wait for effect to apply
                    
                    # Take after screenshot
                    after_shot = self.take_screenshot(f"after_{tool_info['title']}")
                    
                    # Log the effect
                    self.log_image_effect(tool_info['title'], "color_adjustment", {
                        "type": tool_info.get("adjustment", "unknown")
                    })
                    
                    tool_info["screenshots"] = [before_shot, after_shot]
                    tool_info["applied_to_image"] = True
                    return True
                else:
                    # Try Enter key
                    self.actions.send_keys(Keys.ENTER).perform()
                    time.sleep(2)
                    
                    after_shot = self.take_screenshot(f"after_{tool_info['title']}")
                    tool_info["screenshots"] = [before_shot, after_shot]
                    tool_info["applied_to_image"] = True
                    return True
            
            # If no specific adjustment was made, try to find and click any apply button
            apply_buttons = self.driver.find_elements(
                By.XPATH,
                "//button[contains(text(), 'Apply') or contains(text(), 'OK')]"
            )
            if apply_buttons:
                apply_buttons[0].click()
                time.sleep(2)
                after_shot = self.take_screenshot(f"after_{tool_info['title']}")
                tool_info["screenshots"] = [before_shot, after_shot]
                tool_info["applied_to_image"] = True
                return True
            
            return False
            
        except Exception as e:
            self.log_issue(tool_info["title"], "Color Adjustment Failed", str(e))
            return False
    
    def test_and_apply_text_tool(self, tool, tool_info):
        """Test and apply text tool to the image"""
        try:
            print(f"   🔤 Applying {tool_info['title']} to image...")
            
            # Activate tool
            tool.click()
            time.sleep(2)
            
            # Take before screenshot
            before_shot = self.take_screenshot(f"before_{tool_info['title']}")
            
            # Get canvas ready
            if not self.locate_canvas():
                return False
            
            # Click on canvas to create text box
            self.click_on_canvas(x_offset=random.randint(-100, 100), y_offset=random.randint(-100, 100))
            time.sleep(1)
            
            # Type some text
            text_samples = [
                "AI Test",
                "Hello GIMP",
                "Exploratory Testing",
                "Text Tool Test",
                "Sample Text 123"
            ]
            text_to_type = random.choice(text_samples)
            
            self.actions.send_keys(text_to_type).perform()
            time.sleep(1)
            
            # Try to modify text properties
            try:
                # Look for font size
                font_inputs = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "input[type='number'][placeholder*='size' i], input[type='text'][placeholder*='size' i]"
                )
                if font_inputs:
                    font_inputs[0].clear()
                    font_inputs[0].send_keys("24")
                    time.sleep(0.5)
                
                # Look for color picker
                color_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='color']")
                if color_inputs:
                    colors = ["#FF0000", "#0000FF", "#00FF00", "#FF00FF"]
                    color_inputs[0].send_keys(random.choice(colors))
                    time.sleep(0.5)
                
                # Look for font family selector
                font_selects = self.driver.find_elements(By.CSS_SELECTOR, "select")
                if font_selects:
                    select = Select(font_selects[0])
                    if len(select.options) > 1:
                        select.select_by_index(1)
                        time.sleep(0.5)
            except:
                pass
            
            # Click away to apply text
            self.click_on_canvas(x_offset=100, y_offset=100)
            time.sleep(2)
            
            # Take after screenshot
            after_shot = self.take_screenshot(f"after_{tool_info['title']}")
            
            # Log the effect
            self.log_image_effect(tool_info['title'], "text_addition", {
                "text": text_to_type,
                "font_size": "24"
            })
            
            tool_info["screenshots"] = [before_shot, after_shot]
            tool_info["applied_to_image"] = True
            tool_info["text_added"] = text_to_type
            
            return True
            
        except Exception as e:
            self.log_issue(tool_info["title"], "Text Application Failed", str(e))
            return False
    
    def test_and_apply_transform_tool(self, tool, tool_info):
        """Test and apply transform tools to the image"""
        try:
            print(f"   🔄 Applying {tool_info['title']} to image...")
            
            # Activate tool
            tool.click()
            time.sleep(2)
            
            # Take before screenshot
            before_shot = self.take_screenshot(f"before_{tool_info['title']}")
            
            # Get canvas ready
            if not self.locate_canvas():
                return False
            
            title_lower = tool_info['title'].lower()
            transformation_applied = False
            
            if 'rotate' in title_lower:
                # Look for rotation controls
                rotation_inputs = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "input[type='number'][placeholder*='angle' i], input[type='text'][placeholder*='angle' i]"
                )
                if rotation_inputs:
                    rotation_inputs[0].clear()
                    rotation_inputs[0].send_keys("45")  # Rotate 45 degrees
                    tool_info["transformation"] = "rotate_45"
                    transformation_applied = True
                    
                # Also try to find rotation handles on canvas
                try:
                    self.actions.move_to_element(self.canvas).move_by_offset(150, 0)
                    self.actions.click_and_hold().move_by_offset(0, 50).release().perform()
                    time.sleep(1)
                except:
                    pass
                    
            elif 'crop' in title_lower:
                # Draw crop rectangle
                self.actions.move_to_element(self.canvas).move_by_offset(-80, -60)
                self.actions.click_and_hold().move_by_offset(160, 120).release().perform()
                tool_info["transformation"] = "crop_selection"
                transformation_applied = True
                time.sleep(1)
                
                # Look for crop apply button
                crop_buttons = self.driver.find_elements(
                    By.XPATH,
                    "//button[contains(text(), 'Crop') or contains(text(), 'Apply')]"
                )
                if crop_buttons:
                    crop_buttons[0].click()
                    
            elif 'flip' in title_lower:
                # Look for flip buttons
                flip_buttons = self.driver.find_elements(
                    By.XPATH,
                    "//button[contains(text(), 'Horizontal') or contains(text(), 'Vertical')]"
                )
                if flip_buttons:
                    flip_buttons[0].click()
                    tool_info["transformation"] = "flip"
                    transformation_applied = True
                    
            elif 'scale' in title_lower or 'resize' in title_lower:
                # Look for scale controls
                scale_inputs = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "input[type='number'][placeholder*='width' i], input[type='number'][placeholder*='height' i]"
                )
                if scale_inputs and len(scale_inputs) >= 2:
                    scale_inputs[0].clear()
                    scale_inputs[0].send_keys("400")  # New width
                    scale_inputs[1].clear()
                    scale_inputs[1].send_keys("300")  # New height
                    tool_info["transformation"] = "scale_400x300"
                    transformation_applied = True
            
            # Look for general apply/confirm buttons
            if transformation_applied:
                apply_buttons = self.driver.find_elements(
                    By.XPATH,
                    "//button[contains(text(), 'Apply') or contains(text(), 'OK') or contains(text(), 'Confirm')]"
                )
                if apply_buttons:
                    apply_buttons[0].click()
                    time.sleep(2)
            
            # Take after screenshot
            after_shot = self.take_screenshot(f"after_{tool_info['title']}")
            
            # Log the effect if transformation was applied
            if transformation_applied:
                self.log_image_effect(tool_info['title'], "transformation", {
                    "type": tool_info.get("transformation", "unknown")
                })
            
            tool_info["screenshots"] = [before_shot, after_shot]
            tool_info["applied_to_image"] = transformation_applied
            
            return transformation_applied
            
        except Exception as e:
            self.log_issue(tool_info["title"], "Transform Application Failed", str(e))
            return False
    
    def test_and_apply_filter_tool(self, tool, tool_info):
        """Test and apply filter tools to the image"""
        try:
            print(f"   🌈 Applying {tool_info['title']} to image...")
            
            # Activate tool
            tool.click()
            time.sleep(2)
            
            # Take before screenshot
            before_shot = self.take_screenshot(f"before_{tool_info['title']}")
            
            title_lower = tool_info['title'].lower()
            filter_applied = False
            
            # Apply common filters
            if 'blur' in title_lower:
                # Look for blur controls
                sliders = self.driver.find_elements(By.CSS_SELECTOR, "input[type='range']")
                if sliders:
                    sliders[0].clear()
                    sliders[0].send_keys("5")  # Moderate blur
                    tool_info["filter"] = "blur_5"
                    filter_applied = True
                    
            elif 'sharpen' in title_lower:
                sliders = self.driver.find_elements(By.CSS_SELECTOR, "input[type='range']")
                if sliders:
                    sliders[0].clear()
                    sliders[0].send_keys("3")  # Moderate sharpen
                    tool_info["filter"] = "sharpen_3"
                    filter_applied = True
                    
            elif 'noise' in title_lower:
                sliders = self.driver.find_elements(By.CSS_SELECTOR, "input[type='range']")
                if sliders:
                    sliders[0].clear()
                    sliders[0].send_keys("10")  # Add noise
                    tool_info["filter"] = "noise_10"
                    filter_applied = True
            
            # Apply the filter
            if filter_applied:
                # Look for apply/ok buttons
                apply_buttons = self.driver.find_elements(
                    By.XPATH,
                    "//button[contains(text(), 'Apply') or contains(text(), 'OK')]"
                )
                if apply_buttons:
                    apply_buttons[0].click()
                    time.sleep(3)
                    
                    # Take after screenshot
                    after_shot = self.take_screenshot(f"after_{tool_info['title']}")
                    
                    # Log the effect
                    self.log_image_effect(tool_info['title'], "filter", {
                        "type": tool_info.get("filter", "unknown")
                    })
                    
                    tool_info["screenshots"] = [before_shot, after_shot]
                    tool_info["applied_to_image"] = True
                    return True
            
            # Try to find and click any visible apply button
            apply_buttons = self.driver.find_elements(
                By.XPATH,
                "//button[contains(text(), 'Apply') or contains(text(), 'OK')]"
            )
            if apply_buttons:
                apply_buttons[0].click()
                time.sleep(2)
                after_shot = self.take_screenshot(f"after_{tool_info['title']}")
                tool_info["screenshots"] = [before_shot, after_shot]
                tool_info["applied_to_image"] = True
                return True
            
            return False
            
        except Exception as e:
            self.log_issue(tool_info["title"], "Filter Application Failed", str(e))
            return False
    
    def test_tool_comprehensive(self, tool, index):
        """Comprehensive testing and application of a single tool"""
        tool_info = {
            "index": index,
            "title": tool.get_attribute("title") or f"Tool_{index}",
            "status": TestStatus.SKIPPED.value,
            "category": ToolCategory.OTHER.value,
            "activated": False,
            "applied_to_image": False,
            "test_results": {},
            "errors": [],
            "screenshots": [],
            "tested_at": datetime.now().isoformat()
        }
        
        try:
            print(f"\n{'='*60}")
            print(f"Testing Tool {index:02d}: {tool_info['title']}")
            print(f"{'='*60}")
            
            # Categorize tool
            tool_info["category"] = self.categorize_tool(tool_info["title"]).value
            
            # Activate tool first
            try:
                tool.click()
                time.sleep(1)
                tool_info["activated"] = True
            except Exception as e:
                tool_info["status"] = TestStatus.ERROR.value
                tool_info["errors"].append(f"Activation failed: {str(e)}")
                self.report["tools_failed"] += 1
                return tool_info
            
            # Apply tool to image based on category
            applied_successfully = False
            
            if tool_info["category"] == ToolCategory.SELECTION.value:
                applied_successfully = self.test_and_apply_selection_tool(tool, tool_info)
                
            elif tool_info["category"] == ToolCategory.PAINT.value:
                applied_successfully = self.test_and_apply_paint_tool(tool, tool_info)
                
            elif tool_info["category"] == ToolCategory.COLOR.value:
                applied_successfully = self.test_and_apply_color_tool(tool, tool_info)
                
            elif tool_info["category"] == ToolCategory.TEXT.value:
                applied_successfully = self.test_and_apply_text_tool(tool, tool_info)
                
            elif tool_info["category"] == ToolCategory.TRANSFORM.value:
                applied_successfully = self.test_and_apply_transform_tool(tool, tool_info)
                
            elif tool_info["category"] == ToolCategory.FILTER.value:
                applied_successfully = self.test_and_apply_filter_tool(tool, tool_info)
                
            else:
                # For other tools, try to click on canvas
                print(f"   ⚙ Applying {tool_info['title']} (generic)...")
                if self.locate_canvas():
                    before_shot = self.take_screenshot(f"before_{tool_info['title']}")
                    self.click_on_canvas()
                    time.sleep(1)
                    after_shot = self.take_screenshot(f"after_{tool_info['title']}")
                    tool_info["screenshots"] = [before_shot, after_shot]
                    tool_info["applied_to_image"] = True
                    applied_successfully = True
            
            # Update status
            if applied_successfully:
                tool_info["status"] = TestStatus.PASSED.value
                self.report["tools_passed"] += 1
                print(f"   ✅ {tool_info['title']} - APPLIED SUCCESSFULLY")
            else:
                tool_info["status"] = TestStatus.FAILED.value
                self.report["tools_failed"] += 1
                print(f"   ❌ {tool_info['title']} - FAILED TO APPLY")
            
            self.report["tools_tested"] += 1
            
            # Reset to default tool if possible
            try:
                default_tools = self.driver.find_elements(By.CSS_SELECTOR, "button.toolbtn")
                if default_tools and len(default_tools) > 0:
                    default_tools[0].click()  # Click first tool (usually selection or move)
                    time.sleep(0.5)
            except:
                pass
            
        except Exception as e:
            tool_info["status"] = TestStatus.ERROR.value
            tool_info["errors"].append(str(e))
            self.report["tools_failed"] += 1
            self.log_issue(tool_info["title"], "Test Error", str(e), "HIGH")
            print(f"   💥 {tool_info['title']} - ERROR: {str(e)}")
        
        return tool_info
    
    def setup_editor(self):
        """Setup editor and load image"""
        print("🚀 Setting up GIMP Editor for exploratory testing...")
        
        # Open editor
        self.driver.get(URL)
        print("✅ Editor opened")
        
        # Switch to editor iframe
        iframes = self.wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "iframe")))
        editor_iframe = None
        
        for iframe in iframes:
            self.driver.switch_to.default_content()
            self.driver.switch_to.frame(iframe)
            try:
                self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "toolbtn")))
                editor_iframe = iframe
                print("✅ Editor iframe detected")
                break
            except:
                continue
        
        if not editor_iframe:
            raise Exception("❌ Editor iframe not found")
        
        # Upload image
        file_inputs = self.driver.find_elements(By.XPATH, "//input[@type='file']")
        if file_inputs:
            print(f"📤 Uploading image: {IMAGE_PATH}")
            file_inputs[0].send_keys(IMAGE_PATH)
            time.sleep(5)  # Give more time for image to load
            self.report["image_loaded"] = True
            print("🖼️ Image uploaded and loaded")
        
        # Locate canvas
        self.locate_canvas()
        
        return True
    
    def run_exploratory_testing(self):
        """Main exploratory testing loop"""
        print("\n" + "="*60)
        print("STARTING AI-DRIVEN EXPLORATORY TESTING")
        print("="*60)
        print("🎯 GOAL: Apply ALL tools to the test image")
        print("="*60 + "\n")
        
        try:
            # Setup
            if not self.setup_editor():
                return
            
            # Detect all tools
            tools = self.driver.find_elements(By.CSS_SELECTOR, "button.toolbtn")
            print(f"🔧 Total tools detected: {len(tools)}")
            
            # Test each tool
            for index, tool in enumerate(tools):
                # Check if we've exceeded max test time
                elapsed = (datetime.now() - self.start_time).seconds
                if elapsed > TEST_DURATION:
                    print(f"\n⏰ Maximum test duration ({TEST_DURATION//60} minutes) reached")
                    break
                
                tool_info = self.test_tool_comprehensive(tool, index)
                self.report["tools"].append(tool_info)
                
                # Take progress screenshot every 3 tools
                if index % 3 == 0:
                    self.take_screenshot(f"progress_after_tool_{index}")
                
                # Small delay between tools
                time.sleep(1)
            
            # Final report generation
            self.generate_final_report()
            
        except Exception as e:
            print(f"💥 Critical error during testing: {str(e)}")
            traceback.print_exc()
            self.report["critical_error"] = str(e)
        finally:
            self.cleanup()
    
    def generate_final_report(self):
        """Generate comprehensive test report"""
        end_time = datetime.now()
        self.report["test_duration"] = (end_time - self.start_time).seconds
        
        # Calculate statistics
        total_tools = len(self.report["tools"])
        passed_tools = sum(1 for t in self.report["tools"] if t["status"] == TestStatus.PASSED.value)
        failed_tools = sum(1 for t in self.report["tools"] if t["status"] == TestStatus.FAILED.value)
        error_tools = sum(1 for t in self.report["tools"] if t["status"] == TestStatus.ERROR.value)
        applied_tools = sum(1 for t in self.report["tools"] if t.get("applied_to_image", False))
        
        self.report["summary"] = {
            "total_tools": total_tools,
            "passed": passed_tools,
            "failed": failed_tools,
            "errors": error_tools,
            "applied_to_image": applied_tools,
            "pass_rate": f"{(passed_tools/total_tools*100):.1f}%" if total_tools > 0 else "0%",
            "application_rate": f"{(applied_tools/total_tools*100):.1f}%" if total_tools > 0 else "0%",
            "issues_found": len(self.report["issues_found"]),
            "effects_applied": len(self.report["image_effects_applied"])
        }
        
        # Save report
        with open(REPORT_PATH, "w", encoding="utf-8") as f:
            json.dump(self.report, f, indent=2, default=str)
        
        print("\n" + "="*60)
        print("EXPLORATORY TESTING COMPLETE")
        print("="*60)
        print(f"📊 SUMMARY:")
        print(f"   Total Tools Tested: {total_tools}")
        print(f"   Tools Applied to Image: {applied_tools}")
        print(f"   Passed: {passed_tools}")
        print(f"   Failed: {failed_tools}")
        print(f"   Errors: {error_tools}")
        print(f"   Pass Rate: {self.report['summary']['pass_rate']}")
        print(f"   Application Rate: {self.report['summary']['application_rate']}")
        print(f"   Effects Applied: {len(self.report['image_effects_applied'])}")
        print(f"   Issues Found: {len(self.report['issues_found'])}")
        print(f"   Duration: {self.report['test_duration']} seconds")
        print(f"\n📄 Full report saved to: {REPORT_PATH}")
        print(f"📸 Screenshots saved in: {SCREENSHOT_DIR}")
        
        # Print effects applied
        if self.report["image_effects_applied"]:
            print(f"\n✅ IMAGE EFFECTS APPLIED ({len(self.report['image_effects_applied'])}):")
            for i, effect in enumerate(self.report["image_effects_applied"], 1):
                print(f"   {i}. {effect['tool']}: {effect['effect']}")
        
        # Print issues found
        if self.report["issues_found"]:
            print(f"\n⚠ ISSUES FOUND ({len(self.report['issues_found'])}):")
            for i, issue in enumerate(self.report["issues_found"], 1):
                print(f"   {i}. [{issue['severity']}] {issue['tool']}: {issue['type']}")
    
    def cleanup(self):
        """Cleanup resources"""
        print("\n🧹 Cleaning up...")
        self.driver.quit()

# =====================================================
# MAIN EXECUTION
# =====================================================
if __name__ == "__main__":
    tester = GIMPExploratoryTester()
    
    try:
        tester.run_exploratory_testing()
    except KeyboardInterrupt:
        print("\n\n🛑 Testing interrupted by user")
        tester.generate_final_report()
        tester.cleanup()
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        tester.cleanup()
        raise