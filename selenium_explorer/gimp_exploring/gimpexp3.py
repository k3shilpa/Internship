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
from selenium.common.exceptions import MoveTargetOutOfBoundsException, WebDriverException
import pyautogui
from PIL import Image, ImageChops
import math

# =====================================================
# ENUMS & CONFIG
# =====================================================
class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"

class ElementType(Enum):
    TOOL_BUTTON = "tool_button"
    MENU_ITEM = "menu_item"
    SUBMENU_ITEM = "submenu_item"
    DROPDOWN = "dropdown"
    CHECKBOX = "checkbox"
    RADIO_BUTTON = "radio_button"
    SLIDER = "slider"
    COLOR_PICKER = "color_picker"
    BUTTON = "button"
    INPUT_FIELD = "input_field"
    TAB = "tab"
    PANEL = "panel"

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
TEST_DURATION = 3600  # 60 minutes max testing time

if not os.path.exists(IMAGE_PATH):
    raise Exception("❌ Image not found")

os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# =====================================================
# TESTING FRAMEWORK CLASSES
# =====================================================
class GIMPExploratoryTester:
    def __init__(self):
        # Setup Chrome options for better compatibility
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver, 30)
        self.actions = ActionChains(self.driver)
        self.start_time = datetime.now()
        self.canvas = None
        self.canvas_location = None
        self.canvas_size = None
        self.last_screenshot = None
        self.effects_applied = 0
        self.menu_opened = False  # Track if menu is currently open
        
        self.report = {
            "editor": "FixThePhoto Online GIMP",
            "timestamp": self.start_time.isoformat(),
            "image_loaded": False,
            "test_duration": 0,
            "elements_tested": 0,
            "elements_failed": 0,
            "elements_passed": 0,
            "elements_skipped": 0,
            "menu_items": [],
            "tool_buttons": [],
            "ui_elements": [],
            "issues_found": [],
            "image_effects_applied": [],
            "performance_metrics": {}
        }
    
    def safe_click(self, element, description=""):
        """Safely click an element with multiple fallback methods"""
        try:
            if description:
                print(f"   ↪ Clicking: {description}")
            
            # Method 1: Standard click
            element.click()
            return True
        except Exception as e1:
            try:
                # Method 2: JavaScript click
                self.driver.execute_script("arguments[0].click();", element)
                return True
            except Exception as e2:
                try:
                    # Method 3: Actions click
                    self.actions.move_to_element(element).click().perform()
                    return True
                except MoveTargetOutOfBoundsException:
                    try:
                        # Method 4: Scroll into view then click
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                        time.sleep(0.5)
                        element.click()
                        return True
                    except Exception as e4:
                        try:
                            # Method 5: Use pyautogui as last resort
                            location = element.location
                            size = element.size
                            center_x = location['x'] + size['width'] // 2
                            center_y = location['y'] + size['height'] // 2
                            pyautogui.click(center_x, center_y)
                            return True
                        except Exception as e5:
                            print(f"   ⚠ All click methods failed for {description}")
                            return False
    
    def take_screenshot(self, name, wait_before=0):
        """Take screenshot with descriptive name"""
        if wait_before > 0:
            time.sleep(wait_before)
            
        timestamp = datetime.now().strftime("%H%M%S_%f")[:-3]
        filename = f"{SCREENSHOT_DIR}/{name}_{timestamp}.png"
        
        try:
            self.driver.save_screenshot(filename)
            self.last_screenshot = filename
            return filename
        except Exception as e:
            print(f"   ⚠ Screenshot failed: {str(e)}")
            return None
    
    def images_are_different(self, img1_path, img2_path, threshold=5000):
        """Compare two images to see if they're different"""
        try:
            if not os.path.exists(img1_path) or not os.path.exists(img2_path):
                return True
            
            # Load images
            img1 = Image.open(img1_path)
            img2 = Image.open(img2_path)
            
            # Check if images are same size
            if img1.size != img2.size:
                return True
            
            # Convert to RGB if needed
            if img1.mode != img2.mode:
                img1 = img1.convert('RGB')
                img2 = img2.convert('RGB')
            
            # Compare using ImageChops
            diff = ImageChops.difference(img1, img2)
            
            # Calculate difference (sum of all pixel differences)
            diff_value = 0
            diff_data = diff.getdata()
            for pixel in diff_data:
                diff_value += sum(pixel)  # Sum of R+G+B
            
            return diff_value > threshold
            
        except Exception as e:
            print(f"   ⚠ Image comparison failed: {str(e)}")
            return True  # Assume different if comparison fails
    
    def log_issue(self, element_name, element_type, issue_type, description, severity="MEDIUM"):
        """Log an issue found during testing"""
        screenshot = self.take_screenshot(f"issue_{element_name}", wait_before=0.5)
        issue = {
            "element": element_name,
            "type": element_type,
            "issue_type": issue_type,
            "description": description,
            "severity": severity,
            "timestamp": datetime.now().isoformat(),
            "screenshot": screenshot
        }
        self.report["issues_found"].append(issue)
        print(f"   ⚠ ISSUE: {issue_type} - {description}")
    
    def log_image_effect(self, element_name, effect_type, parameters=None, screenshot_before=None, screenshot_after=None):
        """Log successful image effect application"""
        if not screenshot_after:
            screenshot_after = self.take_screenshot(f"effect_{element_name}_{effect_type}", wait_before=1)
        
        visual_change = False
        if screenshot_before and screenshot_after:
            visual_change = self.images_are_different(screenshot_before, screenshot_after)
        
        effect = {
            "element": element_name,
            "effect": effect_type,
            "parameters": parameters or {},
            "timestamp": datetime.now().isoformat(),
            "screenshot_before": screenshot_before,
            "screenshot_after": screenshot_after,
            "visual_change": visual_change
        }
        self.report["image_effects_applied"].append(effect)
        self.effects_applied += 1
        print(f"   ✅ Effect applied: {effect_type} (Visual change: {visual_change})")
    
    def locate_canvas(self):
        """Locate and prepare the canvas for interactions"""
        try:
            # Try to find canvas element
            canvas_selectors = [
                "canvas",
                "#canvas",
                ".canvas",
                "[class*='canvas']",
                "[class*='editor']",
                "[class*='image']"
            ]
            
            for selector in canvas_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            self.canvas = element
                            self.canvas_location = element.location
                            self.canvas_size = element.size
                            return True
                except:
                    continue
            
            # If canvas not found, use viewport center
            viewport_size = self.driver.execute_script("return [window.innerWidth, window.innerHeight];")
            self.canvas_location = {'x': viewport_size[0] // 2, 'y': viewport_size[1] // 2}
            self.canvas_size = {'width': 600, 'height': 400}
            return True
            
        except Exception as e:
            print(f"⚠ Canvas location failed: {str(e)}")
            return False
    
    def click_on_canvas_safe(self, x_offset=0, y_offset=0):
        """Safely click on canvas with multiple fallback methods"""
        try:
            if self.canvas:
                # Method 1: Use JavaScript to click on canvas
                script = """
                var canvas = arguments[0];
                var x = arguments[1];
                var y = arguments[2];
                var rect = canvas.getBoundingClientRect();
                var event = new MouseEvent('click', {
                    view: window,
                    bubbles: true,
                    cancelable: true,
                    clientX: rect.left + rect.width/2 + x,
                    clientY: rect.top + rect.height/2 + y
                });
                canvas.dispatchEvent(event);
                """
                self.driver.execute_script(script, self.canvas, x_offset, y_offset)
                time.sleep(0.5)
                return True
            else:
                # Method 2: Use pyautogui
                screen_width, screen_height = pyautogui.size()
                center_x = screen_width // 2 + x_offset
                center_y = screen_height // 2 + y_offset
                pyautogui.click(center_x, center_y)
                time.sleep(0.5)
                return True
        except Exception as e:
            print(f"⚠ Safe canvas click failed: {str(e)}")
            return False
    
    def ensure_clean_state(self):
        """Try to return to a clean state"""
        print("   🔄 Ensuring clean state...")
        
        # Close any open menus first
        if self.menu_opened:
            self.close_all_menus()
        
        # Try multiple cleanup methods
        cleanup_methods = [
            ("Escape key", self._press_escape),
            ("Undo", self._click_undo),
            ("Default tool", self._select_default_tool),
            ("Canvas click", self._click_canvas_safe)
        ]
        
        for method_name, method in cleanup_methods:
            try:
                if method():
                    print(f"     ↪ {method_name}")
                    time.sleep(0.3)
            except:
                pass
        
        time.sleep(1)
        return True
    
    def _press_escape(self):
        """Press Escape key"""
        self.actions.send_keys(Keys.ESCAPE).perform()
        return True
    
    def _click_undo(self):
        """Click undo button if available"""
        try:
            undo_selectors = [
                "button[title*='Undo' i]",
                "button:contains('Undo')",
                "[class*='undo']"
            ]
            
            for selector in undo_selectors:
                try:
                    undo_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in undo_elements:
                        if element.is_displayed() and element.is_enabled():
                            self.safe_click(element, "Undo button")
                            return True
                except:
                    continue
        except:
            pass
        return False
    
    def _select_default_tool(self):
        """Select default tool (usually Move tool)"""
        try:
            # Look for Move tool
            move_tool_selectors = [
                "button[title*='Move' i]",
                "button[title*='Selection' i]",
                ".toolbtn"  # First tool button
            ]
            
            for selector in move_tool_selectors:
                try:
                    tools = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if tools and tools[0].is_displayed():
                        self.safe_click(tools[0], "Default tool")
                        return True
                except:
                    continue
        except:
            pass
        return False
    
    def _click_canvas_safe(self):
        """Safely click on canvas"""
        try:
            self.click_on_canvas_safe(100, 100)  # Click away from center
            return True
        except:
            return False
    
    def explore_menu_bar_comprehensive(self):
        """Comprehensive menu bar exploration"""
        print("\n" + "="*60)
        print("EXPLORING MENU BAR COMPREHENSIVELY")
        print("="*60)
        
        # First, let's find the top bar where menus might be
        print("🔍 Scanning for menu structure...")
        
        # Look for common menu patterns
        menu_patterns = [
            ("File", ["New", "Open", "Save", "Export", "Close"]),
            ("Edit", ["Undo", "Redo", "Cut", "Copy", "Paste", "Preferences"]),
            ("View", ["Zoom In", "Zoom Out", "Actual Size", "Show Grid", "Show Rulers"]),
            ("Image", ["Image Size", "Canvas Size", "Crop", "Rotate", "Flip"]),
            ("Layer", ["New Layer", "Duplicate Layer", "Merge Layers", "Layer Style"]),
            ("Select", ["All", "None", "Invert", "Feather", "Save Selection"]),
            ("Filter", ["Blur", "Sharpen", "Noise", "Distort", "Render"]),
            ("Tools", ["Brush", "Eraser", "Text", "Gradient", "Crop"]),
            ("Window", ["Layers", "History", "Colors", "Brushes", "Reset Windows"]),
            ("Help", ["About", "Documentation", "Support"])
        ]
        
        found_menus = []
        
        for menu_name, expected_items in menu_patterns:
            print(f"\n📋 Testing menu: {menu_name}")
            
            # Try to find the menu element
            menu_element = None
            
            # Multiple strategies to find menu
            strategies = [
                f"//*[contains(text(), '{menu_name}') and string-length(text()) < 20]",
                f"//button[contains(text(), '{menu_name}')]",
                f"//a[contains(text(), '{menu_name}')]",
                f"//div[contains(text(), '{menu_name}')]",
                f"//span[contains(text(), '{menu_name}')]",
                f"//*[@title='{menu_name}' or contains(@title, '{menu_name}')]",
                f"//*[@aria-label='{menu_name}' or contains(@aria-label, '{menu_name}')]"
            ]
            
            for xpath in strategies:
                try:
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            menu_element = element
                            break
                    if menu_element:
                        break
                except:
                    continue
            
            if not menu_element:
                print(f"   ❌ {menu_name} menu not found")
                continue
            
            # Take screenshot before
            before_shot = self.take_screenshot(f"menu_before_{menu_name}", wait_before=0.5)
            
            # Click the menu
            if not self.safe_click(menu_element, f"{menu_name} menu"):
                print(f"   ❌ Could not click {menu_name} menu")
                continue
            
            time.sleep(1)  # Wait for dropdown to appear
            self.menu_opened = True
            
            # Take screenshot after click
            after_click_shot = self.take_screenshot(f"menu_after_click_{menu_name}", wait_before=0.5)
            
            # Now look for dropdown content
            dropdown_found = False
            dropdown_items = []
            
            # Multiple strategies to find dropdown
            dropdown_selectors = [
                ".dropdown-menu",
                ".menu",
                ".context-menu",
                ".popup",
                "[role='menu']",
                "[class*='dropdown']",
                "[class*='menu']",
                ".MuiMenu-paper",  # Material-UI
                ".ant-dropdown-menu"  # Ant Design
            ]
            
            for selector in dropdown_selectors:
                try:
                    dropdowns = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for dropdown in dropdowns:
                        if dropdown.is_displayed():
                            # Found a dropdown!
                            dropdown_found = True
                            print(f"   ✅ Dropdown found for {menu_name}")
                            
                            # Take screenshot of dropdown
                            dropdown_shot = self.take_screenshot(f"menu_dropdown_{menu_name}", wait_before=0.5)
                            
                            # Try to find menu items in dropdown
                            items = dropdown.find_elements(By.CSS_SELECTOR,
                                "li, a, button, [role='menuitem'], .menu-item, .dropdown-item, .MuiMenuItem-root")
                            
                            if items:
                                print(f"   📋 Found {len(items)} items in dropdown")
                                
                                # Test a few items (max 3 to avoid too many operations)
                                items_to_test = min(3, len(items))
                                for i in range(items_to_test):
                                    item = items[i]
                                    if not item.is_displayed():
                                        continue
                                    
                                    item_text = item.text.strip()
                                    if not item_text or len(item_text) > 50:
                                        continue
                                    
                                    print(f"     ↪ Testing: {item_text}")
                                    
                                    # Take screenshot before item click
                                    item_before = self.take_screenshot(f"menuitem_before_{item_text}", wait_before=0.5)
                                    
                                    # Try to click the item
                                    try:
                                        self.safe_click(item, f"Menu item: {item_text}")
                                        time.sleep(1.5)
                                        
                                        # Take screenshot after
                                        item_after = self.take_screenshot(f"menuitem_after_{item_text}", wait_before=0.5)
                                        
                                        # Check if dialog opened
                                        dialogs = self.driver.find_elements(
                                            By.CSS_SELECTOR,
                                            ".dialog, .modal, [role='dialog'], .MuiDialog-paper"
                                        )
                                        
                                        if dialogs:
                                            print(f"       💬 Dialog opened")
                                            # Close the dialog
                                            self.close_dialog(dialogs[0])
                                        
                                        dropdown_items.append({
                                            "name": item_text,
                                            "clicked": True
                                        })
                                        
                                    except Exception as e:
                                        print(f"     ❌ Menu item failed: {str(e)}")
                                        dropdown_items.append({
                                            "name": item_text,
                                            "clicked": False,
                                            "error": str(e)
                                        })
                                    
                                    # Re-open the menu if needed
                                    if not self.is_menu_open():
                                        self.safe_click(menu_element, f"Re-open {menu_name} menu")
                                        time.sleep(0.5)
                            
                            break  # Found dropdown, stop searching
                except:
                    continue
            
            # Close the menu
            self.close_all_menus()
            
            # Log menu information
            menu_info = {
                "name": menu_name,
                "type": ElementType.MENU_ITEM.value,
                "found": True,
                "clickable": True,
                "opens_dropdown": dropdown_found,
                "dropdown_items_tested": len(dropdown_items),
                "dropdown_items": dropdown_items,
                "screenshots": {
                    "before": before_shot,
                    "after_click": after_click_shot
                },
                "tested_at": datetime.now().isoformat()
            }
            
            self.report["menu_items"].append(menu_info)
            self.report["elements_tested"] += 1
            self.report["elements_passed"] += 1
            
            found_menus.append(menu_name)
            
            # Small delay before next menu
            time.sleep(1)
        
        print(f"\n✅ Found and tested {len(found_menus)} menus: {', '.join(found_menus)}")
    
    def is_menu_open(self):
        """Check if any menu is currently open"""
        try:
            # Check for visible dropdowns
            dropdown_selectors = [
                ".dropdown-menu",
                ".menu",
                "[role='menu']"
            ]
            
            for selector in dropdown_selectors:
                try:
                    dropdowns = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for dropdown in dropdowns:
                        if dropdown.is_displayed():
                            return True
                except:
                    continue
        except:
            pass
        
        return False
    
    def close_all_menus(self):
        """Close all open menus"""
        try:
            # Press Escape multiple times
            for _ in range(3):
                self.actions.send_keys(Keys.ESCAPE).perform()
                time.sleep(0.2)
            
            # Click away
            self.click_on_canvas_safe(200, 200)
            
            self.menu_opened = False
            time.sleep(0.5)
            return True
        except:
            return False
    
    def close_dialog(self, dialog_element):
        """Close a dialog"""
        try:
            # Look for close buttons
            close_selectors = [
                "button:contains('Close')",
                "button:contains('Cancel')",
                "button:contains('OK')",
                ".close",
                "[class*='close']",
                "[aria-label*='Close']",
                "[title*='Close']"
            ]
            
            for selector in close_selectors:
                try:
                    close_buttons = dialog_element.find_elements(By.CSS_SELECTOR, selector)
                    for button in close_buttons:
                        if button.is_displayed() and button.is_enabled():
                            self.safe_click(button, "Dialog close button")
                            time.sleep(0.5)
                            return True
                except:
                    continue
            
            # Press Escape
            self.actions.send_keys(Keys.ESCAPE).perform()
            time.sleep(0.5)
            return True
            
        except Exception as e:
            print(f"   ⚠ Dialog close failed: {str(e)}")
            return False
    
    def explore_toolbar_comprehensive(self):
        """Comprehensive toolbar exploration"""
        print("\n" + "="*60)
        print("EXPLORING TOOLBAR")
        print("="*60)
        
        try:
            # Find all tool buttons
            tools = self.driver.find_elements(By.CSS_SELECTOR, "button.toolbtn")
            print(f"🔧 Total tools detected: {len(tools)}")
            
            for index, tool in enumerate(tools):
                if not tool.is_displayed():
                    continue
                
                try:
                    tool_title = tool.get_attribute("title") or f"Tool_{index}"
                    
                    print(f"\n{'='*40}")
                    print(f"Testing Tool {index:02d}: {tool_title}")
                    print(f"{'='*40}")
                    
                    # Ensure clean state
                    self.ensure_clean_state()
                    
                    # Take before screenshot
                    before_shot = self.take_screenshot(f"tool_before_{tool_title}", wait_before=1)
                    
                    # Click the tool
                    if not self.safe_click(tool, tool_title):
                        print(f"   ❌ Could not click tool: {tool_title}")
                        continue
                    
                    time.sleep(1)
                    
                    # Check activation
                    tool_class = tool.get_attribute("class") or ""
                    is_active = "active" in tool_class.lower()
                    
                    # Apply tool to image
                    applied, effect_type = self.apply_tool_to_image(tool_title, before_shot)
                    
                    # Take after screenshot
                    after_shot = self.take_screenshot(f"tool_after_{tool_title}", wait_before=1)
                    
                    # Check for visual change
                    visual_change = False
                    if before_shot and after_shot:
                        visual_change = self.images_are_different(before_shot, after_shot)
                    
                    # Log tool information
                    tool_info = {
                        "index": index,
                        "title": tool_title,
                        "type": ElementType.TOOL_BUTTON.value,
                        "activated": is_active,
                        "applied_to_image": applied,
                        "visual_change": visual_change,
                        "effect_type": effect_type,
                        "screenshots": {
                            "before": before_shot,
                            "after": after_shot
                        },
                        "tested_at": datetime.now().isoformat()
                    }
                    
                    self.report["tool_buttons"].append(tool_info)
                    self.report["elements_tested"] += 1
                    
                    if applied:
                        self.report["elements_passed"] += 1
                        status = "✅"
                    else:
                        self.report["elements_failed"] += 1
                        status = "❌"
                    
                    visual_indicator = "✨" if visual_change else "⚫"
                    print(f"   {status}{visual_indicator} {tool_title}")
                    
                    # Log effect if visual change
                    if visual_change and applied and before_shot and after_shot:
                        self.log_image_effect(
                            tool_title,
                            effect_type or "tool_application",
                            {"tool_type": self.categorize_tool(tool_title).value},
                            before_shot,
                            after_shot
                        )
                    
                    # Explore tool options
                    self.explore_tool_options(tool_title)
                    
                except Exception as e:
                    print(f"   💥 Tool failed: {str(e)}")
                    self.report["elements_failed"] += 1
                    traceback.print_exc()
                
                time.sleep(1)
                
        except Exception as e:
            print(f"⚠ Toolbar exploration failed: {str(e)}")
            traceback.print_exc()
    
    def categorize_tool(self, tool_title):
        """Categorize tool"""
        if not tool_title:
            return ToolCategory.OTHER
        
        title_lower = tool_title.lower()
        
        if any(word in title_lower for word in ['select', 'rectangle', 'ellipse', 'lasso', 'wand']):
            return ToolCategory.SELECTION
        elif any(word in title_lower for word in ['brush', 'paint', 'eraser', 'heal', 'clone', 'dodge', 'gradient']):
            return ToolCategory.PAINT
        elif any(word in title_lower for word in ['move', 'crop', 'rotate', 'scale']):
            return ToolCategory.TRANSFORM
        elif any(word in title_lower for word in ['text', 'type']):
            return ToolCategory.TEXT
        elif any(word in title_lower for word in ['blur', 'filter']):
            return ToolCategory.FILTER
        else:
            return ToolCategory.OTHER
    
    def apply_tool_to_image(self, tool_title, before_screenshot):
        """Apply tool to image with appropriate action"""
        try:
            if not self.locate_canvas():
                return False, None
            
            tool_lower = tool_title.lower()
            effect_type = None
            
            # Different actions for different tools
            if any(word in tool_lower for word in ['select', 'rectangle', 'ellipse', 'lasso', 'wand']):
                # Selection tools
                self.click_on_canvas_safe(-50, -50)
                time.sleep(0.2)
                # Simulate drag
                pyautogui.mouseDown()
                pyautogui.move(100, 100, duration=0.5)
                pyautogui.mouseUp()
                effect_type = "selection"
                time.sleep(1)
                
            elif any(word in tool_lower for word in ['brush', 'paint', 'heal', 'clone', 'dodge']):
                # Painting tools
                self.click_on_canvas_safe(-30, -30)
                time.sleep(0.2)
                pyautogui.mouseDown()
                pyautogui.move(60, 60, duration=0.5)
                pyautogui.mouseUp()
                effect_type = "painting"
                time.sleep(1)
                
            elif 'eraser' in tool_lower:
                # Eraser
                self.click_on_canvas_safe(-20, -20)
                time.sleep(0.2)
                pyautogui.mouseDown()
                pyautogui.move(40, 40, duration=0.5)
                pyautogui.mouseUp()
                effect_type = "erasing"
                time.sleep(1)
                
            elif 'text' in tool_lower or 'type' in tool_lower:
                # Text tool - special handling
                self.click_on_canvas_safe(0, 0)
                time.sleep(0.5)
                pyautogui.write("Test", interval=0.1)
                time.sleep(1)
                # Click away
                self.click_on_canvas_safe(100, 100)
                effect_type = "text_addition"
                time.sleep(1)
                
            elif 'crop' in tool_lower:
                # Crop tool
                self.click_on_canvas_safe(-40, -40)
                time.sleep(0.2)
                pyautogui.mouseDown()
                pyautogui.move(80, 80, duration=0.5)
                pyautogui.mouseUp()
                effect_type = "crop_selection"
                time.sleep(1)
                
            elif 'gradient' in tool_lower:
                # Gradient tool
                self.click_on_canvas_safe(-40, -40)
                time.sleep(0.2)
                pyautogui.mouseDown()
                pyautogui.move(80, 80, duration=0.5)
                pyautogui.mouseUp()
                effect_type = "gradient"
                time.sleep(1)
                
            elif 'move' in tool_lower or 'hand' in tool_lower:
                # Move/Hand tool
                self.click_on_canvas_safe(0, 0)
                effect_type = "navigation"
                time.sleep(1)
                
            elif 'zoom' in tool_lower:
                # Zoom tool
                self.click_on_canvas_safe(0, 0)
                effect_type = "zoom_in"
                time.sleep(0.5)
                # Zoom out with Alt+click
                pyautogui.keyDown('alt')
                self.click_on_canvas_safe(0, 0)
                pyautogui.keyUp('alt')
                effect_type = "zoom"
                time.sleep(1)
                
            elif 'eyedropper' in tool_lower:
                # Eyedropper
                self.click_on_canvas_safe(0, 0)
                effect_type = "color_pick"
                time.sleep(1)
                
            else:
                # Default action
                self.click_on_canvas_safe(0, 0)
                effect_type = "click"
                time.sleep(1)
            
            return True, effect_type
            
        except Exception as e:
            print(f"   ⚠ Tool application failed: {str(e)}")
            return False, None
    
    def explore_tool_options(self, tool_name):
        """Explore tool options if available"""
        try:
            # Look for options panels
            options_selectors = [
                ".tool-options",
                ".options-panel",
                ".property-panel",
                "[class*='options']",
                "[class*='settings']"
            ]
            
            for selector in options_selectors:
                try:
                    panels = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if panels and panels[0].is_displayed():
                        print(f"   ⚙ {tool_name} has options panel")
                        # Just note it exists, don't interact too much
                        return
                except:
                    continue
                    
        except Exception as e:
            print(f"   ⚙ Options check failed: {str(e)}")
    
    def explore_other_elements(self):
        """Explore other UI elements"""
        print("\n" + "="*60)
        print("EXPLORING OTHER UI ELEMENTS")
        print("="*60)
        
        # Explore panels
        self.explore_panels()
        
        # Explore buttons (excluding menu and tool buttons)
        self.explore_other_buttons()
    
    def explore_panels(self):
        """Explore collapsible panels"""
        try:
            # Look for panel headers
            panel_headers = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".panel-title, .accordion-header, [class*='panel-header'], [class*='header']"
            )
            
            if panel_headers:
                print(f"📦 Found {len(panel_headers)} panels/headers")
                
                # Test a few panels
                for i, header in enumerate(panel_headers[:3]):
                    if not header.is_displayed():
                        continue
                    
                    header_text = header.text.strip()
                    if not header_text or len(header_text) > 30:
                        header_text = f"Panel_{i}"
                    
                    print(f"   📦 Testing: {header_text}")
                    
                    before_shot = self.take_screenshot(f"panel_before_{header_text}")
                    self.safe_click(header, header_text)
                    time.sleep(1)
                    after_shot = self.take_screenshot(f"panel_after_{header_text}")
                    
                    # Log panel
                    panel_info = {
                        "name": header_text,
                        "type": ElementType.PANEL.value,
                        "screenshots": {
                            "before": before_shot,
                            "after": after_shot
                        }
                    }
                    
                    self.report["ui_elements"].append(panel_info)
                    self.report["elements_tested"] += 1
                    
        except Exception as e:
            print(f"⚠ Panel exploration failed: {str(e)}")
    
    def explore_other_buttons(self):
        """Explore other buttons (not menus or tools)"""
        try:
            # Get all buttons
            all_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button")
            
            other_buttons = []
            seen_texts = set()
            
            for button in all_buttons:
                if not button.is_displayed() or not button.is_enabled():
                    continue
                
                # Skip menu and tool buttons
                button_class = button.get_attribute("class") or ""
                if "toolbtn" in button_class or "menu" in button_class.lower():
                    continue
                
                button_text = button.text.strip()
                if not button_text or button_text in seen_texts:
                    continue
                
                # Skip very long text
                if len(button_text) > 30:
                    continue
                
                seen_texts.add(button_text)
                other_buttons.append((button, button_text))
            
            if other_buttons:
                print(f"🔘 Found {len(other_buttons)} other buttons")
                
                # Test a few buttons
                for button, button_text in other_buttons[:5]:
                    print(f"   🔘 Testing: {button_text}")
                    
                    before_shot = self.take_screenshot(f"button_before_{button_text}")
                    self.safe_click(button, button_text)
                    time.sleep(1.5)
                    after_shot = self.take_screenshot(f"button_after_{button_text}")
                    
                    # Check for dialogs
                    dialogs = self.driver.find_elements(
                        By.CSS_SELECTOR,
                        ".dialog, .modal, .popup"
                    )
                    
                    if dialogs:
                        print(f"     💬 Dialog opened")
                        self.close_dialog(dialogs[0])
                    
                    # Log button
                    button_info = {
                        "name": button_text,
                        "type": ElementType.BUTTON.value,
                        "screenshots": {
                            "before": before_shot,
                            "after": after_shot
                        }
                    }
                    
                    self.report["ui_elements"].append(button_info)
                    self.report["elements_tested"] += 1
                    
        except Exception as e:
            print(f"⚠ Button exploration failed: {str(e)}")
    
    def setup_editor(self):
        """Setup editor and load image"""
        print("🚀 Setting up GIMP Editor for exploratory testing...")
        
        # Open editor
        self.driver.get(URL)
        print("✅ Editor opened")
        
        # Switch to editor iframe
        try:
            iframes = self.wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "iframe")))
            for iframe in iframes:
                self.driver.switch_to.default_content()
                self.driver.switch_to.frame(iframe)
                try:
                    # Wait for tool buttons to appear
                    self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.toolbtn")))
                    print("✅ Editor iframe detected and loaded")
                    break
                except:
                    continue
            else:
                raise Exception("❌ Could not find editor iframe")
        except Exception as e:
            print(f"⚠ Iframe detection: {str(e)}")
            # Try without iframe switching
            try:
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.toolbtn")))
                print("✅ Editor loaded (no iframe switching needed)")
            except:
                raise Exception("❌ Editor not loaded properly")
        
        # Upload image
        try:
            file_inputs = self.driver.find_elements(By.XPATH, "//input[@type='file']")
            if file_inputs:
                print(f"📤 Uploading image: {IMAGE_PATH}")
                file_inputs[0].send_keys(IMAGE_PATH)
                time.sleep(10)  # Give plenty of time for image to load
                self.report["image_loaded"] = True
                print("🖼️ Image uploaded and loaded")
            else:
                print("⚠ No file input found - assuming image is already loaded")
        except Exception as e:
            print(f"⚠ Image upload: {str(e)}")
        
        # Take initial screenshot
        self.take_screenshot("initial_state", wait_before=2)
        
        return True
    
    def run_comprehensive_exploration(self):
        """Run comprehensive exploration"""
        print("\n" + "="*60)
        print("STARTING COMPREHENSIVE EXPLORATORY TESTING")
        print("="*60)
        print("🎯 GOAL: Explore ALL UI elements comprehensively")
        print("="*60 + "\n")
        
        try:
            # Setup
            if not self.setup_editor():
                return
            
            # 1. Explore Menu Bar (comprehensively)
            self.explore_menu_bar_comprehensive()
            
            # 2. Explore Toolbar
            self.explore_toolbar_comprehensive()
            
            # 3. Explore Other Elements
            self.explore_other_elements()
            
            # Final report
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
        total_menu_items = len(self.report["menu_items"])
        total_tools = len(self.report["tool_buttons"])
        total_ui_elements = len(self.report["ui_elements"])
        total_elements = total_menu_items + total_tools + total_ui_elements
        
        # Count tools with changes
        tools_with_changes = sum(1 for t in self.report["tool_buttons"] if t.get("visual_change", False))
        tools_applied = sum(1 for t in self.report["tool_buttons"] if t.get("applied_to_image", False))
        
        # Count menus with dropdowns
        menus_with_dropdowns = sum(1 for m in self.report["menu_items"] if m.get("opens_dropdown", False))
        
        self.report["summary"] = {
            "total_elements_tested": total_elements,
            "menu_items": total_menu_items,
            "menus_with_dropdowns": menus_with_dropdowns,
            "tool_buttons": total_tools,
            "tools_applied": tools_applied,
            "tools_with_visual_changes": tools_with_changes,
            "ui_elements": total_ui_elements,
            "elements_passed": self.report["elements_passed"],
            "elements_failed": self.report["elements_failed"],
            "success_rate": f"{(self.report['elements_passed']/max(total_elements, 1)*100):.1f}%",
            "menu_dropdown_rate": f"{(menus_with_dropdowns/max(total_menu_items, 1)*100):.1f}%",
            "visual_change_rate": f"{(tools_with_changes/max(total_tools, 1)*100):.1f}%",
            "issues_found": len(self.report["issues_found"]),
            "effects_applied": len(self.report["image_effects_applied"])
        }
        
        # Save report
        with open(REPORT_PATH, "w", encoding="utf-8") as f:
            json.dump(self.report, f, indent=2, default=str)
        
        print("\n" + "="*60)
        print("COMPREHENSIVE EXPLORATORY TESTING COMPLETE")
        print("="*60)
        print(f"📊 SUMMARY:")
        print(f"   Total Elements Tested: {total_elements}")
        print(f"   Menu Items: {total_menu_items}")
        print(f"   Menus with Dropdowns: {menus_with_dropdowns}")
        print(f"   Tool Buttons: {total_tools}")
        print(f"   Tools Applied to Image: {tools_applied}")
        print(f"   Tools with Visual Changes: {tools_with_changes}")
        print(f"   UI Elements: {total_ui_elements}")
        print(f"   Passed: {self.report['elements_passed']}")
        print(f"   Failed: {self.report['elements_failed']}")
        print(f"   Success Rate: {self.report['summary']['success_rate']}")
        print(f"   Menu Dropdown Rate: {self.report['summary']['menu_dropdown_rate']}")
        print(f"   Visual Change Rate: {self.report['summary']['visual_change_rate']}")
        print(f"   Effects Applied: {len(self.report['image_effects_applied'])}")
        print(f"   Issues Found: {len(self.report['issues_found'])}")
        print(f"   Duration: {self.report['test_duration']} seconds")
        print(f"\n📄 Full report saved to: {REPORT_PATH}")
        print(f"📸 Screenshots saved in: {SCREENSHOT_DIR}")
        
        # Print menu summary
        if self.report["menu_items"]:
            print(f"\n📋 MENU SUMMARY:")
            for menu in self.report["menu_items"]:
                dropdown_status = "✅" if menu.get("opens_dropdown") else "❌"
                items_tested = menu.get("dropdown_items_tested", 0)
                print(f"   {dropdown_status} {menu['name']}: {items_tested} items tested")
        
        # Print tool summary
        if self.report["tool_buttons"]:
            print(f"\n🔧 TOOL SUMMARY (first 10):")
            for i, tool in enumerate(self.report["tool_buttons"][:10], 1):
                applied = "✅" if tool.get("applied_to_image") else "❌"
                visual = "✨" if tool.get("visual_change") else "⚫"
                print(f"   {i}. {applied}{visual} {tool['title']}")
    
    def cleanup(self):
        """Cleanup resources"""
        print("\n🧹 Cleaning up...")
        try:
            self.driver.quit()
        except:
            pass

# =====================================================
# MAIN EXECUTION
# =====================================================
if __name__ == "__main__":
    tester = GIMPExploratoryTester()
    
    try:
        tester.run_comprehensive_exploration()
    except KeyboardInterrupt:
        print("\n\n🛑 Testing interrupted by user")
        tester.generate_final_report()
        tester.cleanup()
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        traceback.print_exc()
        tester.cleanup()