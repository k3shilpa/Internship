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
import pyautogui  # For more reliable clicking

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
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver, 40)
        self.actions = ActionChains(self.driver)
        self.start_time = datetime.now()
        self.canvas = None
        self.canvas_location = None
        self.canvas_size = None
        self.last_screenshot = None
        self.effects_applied = 0
        
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
    
    def take_screenshot(self, name, wait_before=0):
        """Take screenshot with descriptive name"""
        if wait_before > 0:
            time.sleep(wait_before)
            
        timestamp = datetime.now().strftime("%H%M%S_%f")[:-3]
        filename = f"{SCREENSHOT_DIR}/{name}_{timestamp}.png"
        self.driver.save_screenshot(filename)
        self.last_screenshot = filename
        return filename
    
    def compare_screenshots(self, screenshot1, screenshot2):
        """Simple screenshot comparison (returns True if different)"""
        try:
            # Simple file size comparison as a basic check
            size1 = os.path.getsize(screenshot1) if os.path.exists(screenshot1) else 0
            size2 = os.path.getsize(screenshot2) if os.path.exists(screenshot2) else 0
            return abs(size1 - size2) > 1000  # If file sizes differ significantly
        except:
            return True  # Assume different if comparison fails
    
    def log_issue(self, element_name, element_type, issue_type, description, severity="MEDIUM"):
        """Log an issue found during testing"""
        issue = {
            "element": element_name,
            "type": element_type,
            "issue_type": issue_type,
            "description": description,
            "severity": severity,
            "timestamp": datetime.now().isoformat(),
            "screenshot": self.take_screenshot(f"issue_{element_name}")
        }
        self.report["issues_found"].append(issue)
        print(f"   ⚠ ISSUE: {issue_type} - {description}")
    
    def log_image_effect(self, element_name, effect_type, parameters=None, screenshot_before=None, screenshot_after=None):
        """Log successful image effect application"""
        if not screenshot_after:
            screenshot_after = self.take_screenshot(f"effect_{element_name}_{effect_type}")
        
        effect = {
            "element": element_name,
            "effect": effect_type,
            "parameters": parameters or {},
            "timestamp": datetime.now().isoformat(),
            "screenshot_before": screenshot_before,
            "screenshot_after": screenshot_after,
            "visual_change": self.compare_screenshots(screenshot_before, screenshot_after) if screenshot_before else False
        }
        self.report["image_effects_applied"].append(effect)
        self.effects_applied += 1
        print(f"   ✅ Effect applied: {effect_type} (Visual change: {effect['visual_change']})")
    
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
                return True
            else:
                # Use approximate center of screen
                self.canvas_location = {'x': 400, 'y': 300}
                self.canvas_size = {'width': 800, 'height': 600}
                return True
                
        except Exception as e:
            print(f"⚠ Canvas location failed: {str(e)}")
            return False
    
    def click_on_canvas(self, x_offset=0, y_offset=0, use_pyautogui=False):
        """Click on canvas with optional offset from center"""
        try:
            if use_pyautogui and self.canvas:
                # Use pyautogui for more reliable clicking
                canvas_center_x = self.canvas_location['x'] + self.canvas_size['width'] // 2 + x_offset
                canvas_center_y = self.canvas_location['y'] + self.canvas_size['height'] // 2 + y_offset
                pyautogui.click(canvas_center_x, canvas_center_y)
                time.sleep(0.5)
                return True
            elif self.canvas:
                # Use Selenium actions
                self.actions.move_to_element(self.canvas).move_by_offset(x_offset, y_offset).click().perform()
                time.sleep(0.5)
                return True
            else:
                # Fallback to JavaScript click
                self.driver.execute_script(f"""
                    var event = new MouseEvent('click', {{
                        view: window,
                        bubbles: true,
                        cancelable: true,
                        clientX: {400 + x_offset},
                        clientY: {300 + y_offset}
                    }});
                    document.elementFromPoint({400 + x_offset}, {300 + y_offset}).dispatchEvent(event);
                """)
                time.sleep(0.5)
                return True
        except Exception as e:
            print(f"⚠ Canvas click failed: {str(e)}")
            return False
    
    def ensure_clean_state(self):
        """Try to return to a clean state"""
        print("   🔄 Ensuring clean state...")
        
        # Try multiple cleanup methods
        cleanup_attempts = [
            ("Escape key", self._try_escape_key),
            ("Undo button", self._try_undo_button),
            ("Default tool", self._try_default_tool),
            ("Canvas click", self._try_canvas_click)
        ]
        
        for method_name, method in cleanup_attempts:
            try:
                if method():
                    print(f"     ↪ Cleaned with: {method_name}")
                    time.sleep(0.5)
            except Exception as e:
                print(f"     ⚠ {method_name} failed: {str(e)}")
        
        time.sleep(1)
        return True
    
    def _try_escape_key(self):
        """Try pressing Escape key"""
        self.actions.send_keys(Keys.ESCAPE).perform()
        return True
    
    def _try_undo_button(self):
        """Try clicking undo button"""
        undo_selectors = [
            "button[title*='Undo' i]",
            "button:contains('Undo')",
            "[class*='undo'] button",
            "button[class*='undo']"
        ]
        
        for selector in undo_selectors:
            try:
                undo_buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for button in undo_buttons:
                    if button.is_displayed() and button.is_enabled():
                        button.click()
                        return True
            except:
                continue
        
        return False
    
    def _try_default_tool(self):
        """Try clicking default tool"""
        try:
            default_tools = self.driver.find_elements(By.CSS_SELECTOR, "button.toolbtn")
            for tool in default_tools:
                if tool.is_displayed() and tool.is_enabled():
                    if "Move" in (tool.get_attribute("title") or ""):
                        tool.click()
                        return True
            # If no move tool, click first tool
            if default_tools and default_tools[0].is_displayed():
                default_tools[0].click()
                return True
        except:
            pass
        return False
    
    def _try_canvas_click(self):
        """Try clicking on canvas"""
        try:
            if self.locate_canvas():
                self.click_on_canvas(0, 0)
                return True
        except:
            pass
        return False
    
    def explore_menu_bar(self):
        """Explore all menu bar items (File, Edit, View, etc.)"""
        print("\n" + "="*60)
        print("EXPLORING MENU BAR")
        print("="*60)
        
        # First, let's try to find the actual menu structure
        print("🔍 Looking for menu structure...")
        
        # Take a screenshot of the current state
        self.take_screenshot("menu_exploration_start")
        
        # List of expected menu items
        expected_menus = ["File", "Edit", "View", "Image", "Layer", "Select", "Filter", "Tools", "Help", "Window"]
        
        menus_found = []
        
        for menu_text in expected_menus:
            try:
                # Look for elements that might be menus
                menu_elements = self.driver.find_elements(
                    By.XPATH,
                    f"//*[contains(text(), '{menu_text}') or contains(@title, '{menu_text}') or contains(@aria-label, '{menu_text}')]"
                )
                
                for element in menu_elements:
                    if element.is_displayed() and element.is_enabled():
                        print(f"   📝 Found menu: {menu_text}")
                        
                        # Take before screenshot
                        before_shot = self.take_screenshot(f"menu_before_{menu_text}")
                        
                        # Hover over the menu first (some menus need hover to show dropdown)
                        try:
                            self.actions.move_to_element(element).perform()
                            time.sleep(0.5)
                        except:
                            pass
                        
                        # Click the menu
                        try:
                            element.click()
                        except:
                            # Try JavaScript click as fallback
                            self.driver.execute_script("arguments[0].click();", element)
                        
                        time.sleep(1.5)  # Wait for dropdown to appear
                        
                        # Take screenshot to see what opened
                        after_shot = self.take_screenshot(f"menu_after_{menu_text}")
                        
                        # Look for dropdown menu that appeared
                        dropdowns = self.driver.find_elements(
                            By.CSS_SELECTOR,
                            ".dropdown-menu, .submenu, [role='menu'], [class*='dropdown'], .menu-list, ul.menu"
                        )
                        
                        if dropdowns:
                            print(f"   ➡ Dropdown menu appeared for {menu_text}")
                            self.explore_dropdown_menu(menu_text, dropdowns[0])
                        else:
                            # Maybe it opened a dialog instead
                            dialogs = self.driver.find_elements(
                                By.CSS_SELECTOR,
                                ".dialog, .modal, .popup, [role='dialog']"
                            )
                            if dialogs:
                                print(f"   ➡ Dialog opened for {menu_text}")
                                self.explore_dialog(f"Menu: {menu_text}", dialogs[0])
                        
                        # Log the menu item
                        menu_info = {
                            "name": menu_text,
                            "type": ElementType.MENU_ITEM.value,
                            "opens_dropdown": len(dropdowns) > 0,
                            "opens_dialog": len(dialogs) > 0,
                            "screenshots": [before_shot, after_shot],
                            "tested_at": datetime.now().isoformat()
                        }
                        
                        self.report["menu_items"].append(menu_info)
                        self.report["elements_tested"] += 1
                        self.report["elements_passed"] += 1
                        
                        menus_found.append(menu_text)
                        
                        # Close any open menus/dialogs
                        self._close_all_menus()
                        
                        # Small delay before next menu
                        time.sleep(1)
                        
                        break  # Found this menu, move to next
                        
            except Exception as e:
                print(f"   ❌ Menu {menu_text} failed: {str(e)}")
                self.report["elements_failed"] += 1
        
        print(f"\n✅ Found {len(menus_found)} menus: {', '.join(menus_found)}")
    
    def explore_dropdown_menu(self, parent_name, dropdown_element):
        """Explore items in a dropdown menu"""
        try:
            # Find all menu items in dropdown
            menu_items = dropdown_element.find_elements(
                By.CSS_SELECTOR,
                "li, a, button, [role='menuitem'], .menu-item, .dropdown-item"
            )
            
            if not menu_items:
                # Try alternative selectors
                menu_items = dropdown_element.find_elements(By.CSS_SELECTOR, "*")
            
            print(f"   📋 Dropdown has {len(menu_items)} items")
            
            items_to_test = min(5, len(menu_items))  # Test max 5 items to avoid too many operations
            
            for idx in range(items_to_test):
                item = menu_items[idx]
                
                if not item.is_displayed():
                    continue
                
                try:
                    item_text = item.text.strip()
                    if not item_text or len(item_text) > 50:  # Skip very long text or empty
                        item_text = f"Item_{idx}"
                    
                    # Skip separators or disabled items
                    if not item_text or item_text == "---" or "separator" in (item.get_attribute("class") or ""):
                        continue
                    
                    print(f"     ↪ Testing: {item_text}")
                    
                    # Take before screenshot
                    before_shot = self.take_screenshot(f"dropdown_before_{item_text}")
                    
                    # Hover first
                    try:
                        self.actions.move_to_element(item).perform()
                        time.sleep(0.3)
                    except:
                        pass
                    
                    # Click the item
                    try:
                        item.click()
                    except:
                        self.driver.execute_script("arguments[0].click();", item)
                    
                    time.sleep(2)  # Wait for action to complete
                    
                    # Take after screenshot
                    after_shot = self.take_screenshot(f"dropdown_after_{item_text}")
                    
                    # Check if this opened a submenu or dialog
                    sub_dropdowns = self.driver.find_elements(
                        By.CSS_SELECTOR,
                        ".dropdown-menu, .submenu"
                    )
                    
                    dialogs = self.driver.find_elements(
                        By.CSS_SELECTOR,
                        ".dialog, .modal, .popup"
                    )
                    
                    # Log the menu item
                    item_info = {
                        "parent": parent_name,
                        "name": item_text,
                        "type": ElementType.SUBMENU_ITEM.value,
                        "opens_submenu": len(sub_dropdowns) > 0,
                        "opens_dialog": len(dialogs) > 0,
                        "screenshots": [before_shot, after_shot]
                    }
                    
                    self.report["ui_elements"].append(item_info)
                    
                    # If dialog opened, explore it briefly
                    if dialogs:
                        print(f"       💬 Dialog opened")
                        self.explore_dialog_briefly(f"{parent_name} > {item_text}", dialogs[0])
                    
                    # Close any dialogs
                    self._close_all_menus()
                    
                    # Check if image was modified
                    if self.detect_image_change(before_shot, after_shot):
                        self.log_image_effect(
                            f"{parent_name} > {item_text}",
                            "menu_action",
                            {},
                            before_shot,
                            after_shot
                        )
                    
                except Exception as e:
                    print(f"     ❌ Dropdown item failed: {str(e)}")
                
                time.sleep(1)
                
        except Exception as e:
            print(f"   ⚠ Dropdown exploration failed: {str(e)}")
    
    def explore_dialog_briefly(self, source_name, dialog_element):
        """Briefly explore a dialog (just click OK/Apply if available)"""
        try:
            # Look for common dialog buttons
            button_selectors = [
                "button:contains('OK')",
                "button:contains('Apply')",
                "button:contains('Save')",
                "button:contains('Confirm')",
                "button[type='submit']"
            ]
            
            for selector in button_selectors:
                try:
                    buttons = dialog_element.find_elements(By.CSS_SELECTOR, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            print(f"       ↪ Clicking dialog button: {button.text.strip()}")
                            button.click()
                            time.sleep(1)
                            return True
                except:
                    continue
            
            # If no action buttons, try to close
            self._try_close_dialog(dialog_element)
            
        except Exception as e:
            print(f"       ⚠ Dialog exploration failed: {str(e)}")
        
        return False
    
    def detect_image_change(self, before_screenshot, after_screenshot):
        """Detect if image was modified by comparing screenshots"""
        try:
            return self.compare_screenshots(before_screenshot, after_screenshot)
        except:
            return False
    
    def _close_all_menus(self):
        """Close all open menus and dialogs"""
        # Try Escape key multiple times
        for _ in range(3):
            try:
                self.actions.send_keys(Keys.ESCAPE).perform()
                time.sleep(0.3)
            except:
                pass
        
        # Click on canvas to dismiss menus
        try:
            self.click_on_canvas(200, 200)  # Click away from menus
            time.sleep(0.5)
        except:
            pass
        
        return True
    
    def _try_close_dialog(self, dialog_element):
        """Try to close a dialog"""
        try:
            close_selectors = [
                "button:contains('Close')",
                "button:contains('Cancel')",
                ".close",
                "[class*='close']",
                "button[title*='Close']"
            ]
            
            for selector in close_selectors:
                try:
                    close_buttons = dialog_element.find_elements(By.CSS_SELECTOR, selector)
                    for button in close_buttons:
                        if button.is_displayed() and button.is_enabled():
                            button.click()
                            time.sleep(0.5)
                            return True
                except:
                    continue
        except:
            pass
        
        return False
    
    def explore_toolbar(self):
        """Explore all tool buttons in sidebar"""
        print("\n" + "="*60)
        print("EXPLORING TOOLBAR")
        print("="*60)
        
        try:
            # Find tool buttons
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
                    try:
                        tool.click()
                    except:
                        self.driver.execute_script("arguments[0].click();", tool)
                    
                    time.sleep(1)
                    
                    # Check if tool activated
                    tool_class = tool.get_attribute("class") or ""
                    is_active = "active" in tool_class.lower()
                    
                    # Try to use the tool on canvas
                    applied, effect_type = self.try_apply_tool_with_effect(tool_title, before_shot)
                    
                    # Take after screenshot
                    after_shot = self.take_screenshot(f"tool_after_{tool_title}", wait_before=1)
                    
                    # Check for visual change
                    visual_change = self.detect_image_change(before_shot, after_shot)
                    
                    # Log tool information
                    tool_info = {
                        "index": index,
                        "title": tool_title,
                        "type": ElementType.TOOL_BUTTON.value,
                        "activated": is_active,
                        "applied_to_image": applied,
                        "visual_change": visual_change,
                        "effect_type": effect_type,
                        "screenshots": [before_shot, after_shot],
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
                    
                    print(f"   {status} {tool_title} - Applied: {applied}, Visual change: {visual_change}")
                    
                    # Log effect if visual change detected
                    if visual_change and applied:
                        self.log_image_effect(
                            tool_title,
                            effect_type or "tool_application",
                            {"tool_type": self.categorize_tool(tool_title).value},
                            before_shot,
                            after_shot
                        )
                    
                    # Clean up
                    self.ensure_clean_state()
                    
                    # Explore tool options if any
                    self.explore_tool_options(tool_title)
                    
                except Exception as e:
                    print(f"   💥 Tool failed: {str(e)}")
                    self.report["elements_failed"] += 1
                    self.log_issue(tool_title, "tool_button", "Test Failed", str(e), "HIGH")
                
                time.sleep(1)
                
        except Exception as e:
            print(f"⚠ Toolbar exploration failed: {str(e)}")
    
    def categorize_tool(self, tool_title):
        """Categorize tool based on its title/function"""
        if not tool_title:
            return ToolCategory.OTHER
        
        title_lower = tool_title.lower()
        
        if any(word in title_lower for word in ['select', 'rectangle', 'ellipse', 'free', 'fuzzy', 'lasso', 'wand']):
            return ToolCategory.SELECTION
        elif any(word in title_lower for word in ['brush', 'pencil', 'eraser', 'bucket', 'gradient', 'paint', 'heal', 'clone', 'dodge']):
            return ToolCategory.PAINT
        elif any(word in title_lower for word in ['move', 'rotate', 'scale', 'shear', 'perspective', 'flip', 'crop']):
            return ToolCategory.TRANSFORM
        elif any(word in title_lower for word in ['color', 'hue', 'saturation', 'brightness', 'levels', 'curves']):
            return ToolCategory.COLOR
        elif any(word in title_lower for word in ['text', 'type']):
            return ToolCategory.TEXT
        elif any(word in title_lower for word in ['filter', 'blur', 'sharpen', 'noise', 'edge']):
            return ToolCategory.FILTER
        else:
            return ToolCategory.OTHER
    
    def try_apply_tool_with_effect(self, tool_title, before_screenshot):
        """Try to apply a tool to the canvas and detect effect"""
        try:
            if not self.locate_canvas():
                return False, None
            
            tool_lower = tool_title.lower()
            effect_type = None
            
            # Different actions for different tool types
            if any(word in tool_lower for word in ['select', 'rectangle', 'ellipse', 'free', 'fuzzy', 'lasso', 'wand']):
                # Selection tool - draw selection
                self.actions.move_to_element(self.canvas).move_by_offset(-50, -50)
                self.actions.click_and_hold().move_by_offset(100, 100).release().perform()
                effect_type = "selection"
                time.sleep(1.5)
                
            elif any(word in tool_lower for word in ['brush', 'paint']):
                # Drawing tool - draw a line
                self.actions.move_to_element(self.canvas).move_by_offset(-30, -30)
                self.actions.click_and_hold().move_by_offset(60, 60).release().perform()
                effect_type = "painting"
                time.sleep(1.5)
                
            elif 'eraser' in tool_lower:
                # Eraser tool
                self.actions.move_to_element(self.canvas).move_by_offset(-20, -20)
                self.actions.click_and_hold().move_by_offset(40, 40).release().perform()
                effect_type = "erasing"
                time.sleep(1.5)
                
            elif any(word in tool_lower for word in ['text', 'type']):
                # Text tool - special handling for canvas error
                try:
                    # Click on canvas using JavaScript to avoid move target out of bounds
                    self.driver.execute_script("""
                        var canvas = document.querySelector('canvas');
                        if (canvas) {
                            var rect = canvas.getBoundingClientRect();
                            var event = new MouseEvent('click', {
                                view: window,
                                bubbles: true,
                                cancelable: true,
                                clientX: rect.left + rect.width/2,
                                clientY: rect.top + rect.height/2
                            });
                            canvas.dispatchEvent(event);
                        }
                    """)
                    time.sleep(0.5)
                    
                    # Type some text
                    self.actions.send_keys("Test").perform()
                    time.sleep(1)
                    
                    # Click away
                    self.click_on_canvas(100, 100, use_pyautogui=True)
                    effect_type = "text_addition"
                    time.sleep(1.5)
                except Exception as e:
                    print(f"   ⚠ Text tool workaround failed: {str(e)}")
                    return False, None
                
            elif 'crop' in tool_lower:
                # Crop tool
                self.actions.move_to_element(self.canvas).move_by_offset(-40, -40)
                self.actions.click_and_hold().move_by_offset(80, 80).release().perform()
                effect_type = "crop_selection"
                time.sleep(1.5)
                
            elif 'gradient' in tool_lower:
                # Gradient tool
                self.actions.move_to_element(self.canvas).move_by_offset(-40, -40)
                self.actions.click_and_hold().move_by_offset(80, 80).release().perform()
                effect_type = "gradient"
                time.sleep(1.5)
                
            elif any(word in tool_lower for word in ['move', 'hand']):
                # Move/Hand tool - just click
                self.click_on_canvas()
                effect_type = "navigation"
                time.sleep(1)
                
            elif any(word in tool_lower for word in ['zoom']):
                # Zoom tool - click to zoom in
                self.click_on_canvas()
                effect_type = "zoom"
                time.sleep(1)
                # Zoom out
                self.actions.key_down(Keys.ALT).click().key_up(Keys.ALT).perform()
                time.sleep(1)
                
            else:
                # Generic tool - just click
                self.click_on_canvas()
                effect_type = "generic"
                time.sleep(1)
            
            return True, effect_type
                
        except Exception as e:
            print(f"   ⚠ Tool application failed: {str(e)}")
            return False, None
    
    def explore_tool_options(self, tool_name):
        """Explore options panel for a tool"""
        try:
            # Look for tool options panel
            options_selectors = [
                ".tool-options",
                ".options-panel", 
                "[class*='options']",
                "[class*='settings']",
                ".property-panel"
            ]
            
            for selector in options_selectors:
                try:
                    options_panels = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if options_panels:
                        panel = options_panels[0]
                        if panel.is_displayed():
                            print(f"   ⚙ {tool_name} has options panel")
                            self.explore_options_panel(tool_name, panel)
                            break
                except:
                    continue
                    
        except Exception as e:
            print(f"   ⚠ Options exploration failed: {str(e)}")
    
    def explore_options_panel(self, tool_name, panel):
        """Explore options in a panel"""
        try:
            # Find interactive elements
            options = panel.find_elements(By.CSS_SELECTOR,
                "input, select, button, [role='slider'], [role='checkbox'], label")
            
            interactive_options = []
            for option in options:
                if option.is_displayed() and option.is_enabled():
                    interactive_options.append(option)
            
            print(f"   🔧 Found {len(interactive_options)} options")
            
            # Test a few options (max 3 to avoid too many changes)
            for idx, option in enumerate(interactive_options[:3]):
                try:
                    option_type = option.tag_name.lower()
                    option_name = option.get_attribute("title") or option.get_attribute("aria-label") or option.text.strip() or f"Option_{idx}"
                    
                    print(f"     ↪ Testing option: {option_name} ({option_type})")
                    
                    before_shot = self.take_screenshot(f"option_before_{option_name}", wait_before=0.5)
                    
                    # Interact based on type
                    if option_type == "input":
                        input_type = option.get_attribute("type")
                        if input_type == "range":
                            # Slider
                            current = option.get_attribute("value") or "50"
                            new_val = str(random.randint(20, 80))
                            self.driver.execute_script(f"arguments[0].value = '{new_val}';", option)
                            self.driver.execute_script("arguments[0].dispatchEvent(new Event('input'));", option)
                            self.driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", option)
                            
                        elif input_type == "color":
                            # Color picker
                            colors = ["#FF0000", "#00FF00", "#0000FF"]
                            option.send_keys(random.choice(colors))
                            
                        elif input_type in ["text", "number"]:
                            # Text/number input
                            if option.is_enabled():
                                option.clear()
                                option.send_keys("25" if input_type == "number" else "Test")
                                
                    elif option_type == "select":
                        # Dropdown
                        select = Select(option)
                        if len(select.options) > 1:
                            select.select_by_index(1)
                            
                    elif option_type == "button":
                        # Button (avoid apply/ok buttons)
                        btn_text = option.text.strip().lower()
                        if "apply" not in btn_text and "ok" not in btn_text:
                            option.click()
                    
                    after_shot = self.take_screenshot(f"option_after_{option_name}", wait_before=0.5)
                    
                    # Check for visual change
                    visual_change = self.detect_image_change(before_shot, after_shot)
                    
                    option_info = {
                        "tool": tool_name,
                        "name": option_name,
                        "type": option_type,
                        "visual_change": visual_change,
                        "screenshots": [before_shot, after_shot]
                    }
                    
                    self.report["ui_elements"].append(option_info)
                    
                    if visual_change:
                        self.log_image_effect(
                            f"{tool_name} - {option_name}",
                            "option_change",
                            {},
                            before_shot,
                            after_shot
                        )
                    
                except Exception as e:
                    print(f"     ❌ Option failed: {str(e)}")
                
                time.sleep(0.5)
                
        except Exception as e:
            print(f"   ⚠ Options panel exploration failed: {str(e)}")
    
    def explore_other_ui_elements(self):
        """Explore other UI elements"""
        print("\n" + "="*60)
        print("EXPLORING OTHER UI ELEMENTS")
        print("="*60)
        
        # Explore panels (like layers, history, etc.)
        self.explore_panels()
        
        # Explore general buttons
        self.explore_general_buttons()
    
    def explore_panels(self):
        """Explore collapsible panels"""
        try:
            panel_headers = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".panel-header, .accordion-header, [class*='panel-title'], [class*='header']"
            )
            
            if panel_headers:
                print(f"📦 Found {len(panel_headers)} panels")
                
                for idx, header in enumerate(panel_headers[:3]):  # Test max 3 panels
                    if not header.is_displayed():
                        continue
                    
                    try:
                        panel_name = header.text.strip() or f"Panel_{idx}"
                        if not panel_name or len(panel_name) > 30:
                            continue
                        
                        print(f"   📦 Testing panel: {panel_name}")
                        
                        before_shot = self.take_screenshot(f"panel_before_{panel_name}")
                        header.click()
                        time.sleep(1)
                        after_shot = self.take_screenshot(f"panel_after_{panel_name}")
                        
                        panel_info = {
                            "name": panel_name,
                            "type": ElementType.PANEL.value,
                            "screenshots": [before_shot, after_shot]
                        }
                        
                        self.report["ui_elements"].append(panel_info)
                        self.report["elements_tested"] += 1
                        
                    except Exception as e:
                        print(f"   ❌ Panel failed: {str(e)}")
                    
                    time.sleep(0.5)
                    
        except Exception as e:
            print(f"⚠ Panel exploration failed: {str(e)}")
    
    def explore_general_buttons(self):
        """Explore general buttons not in menus or toolbars"""
        try:
            # Find buttons excluding tool buttons
            all_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button")
            
            general_buttons = []
            seen_texts = set()
            
            for button in all_buttons:
                if not button.is_displayed() or not button.is_enabled():
                    continue
                
                # Skip tool buttons
                if "toolbtn" in (button.get_attribute("class") or ""):
                    continue
                
                button_text = button.text.strip()
                if not button_text or button_text in seen_texts:
                    continue
                
                # Skip very long text
                if len(button_text) > 30:
                    continue
                
                seen_texts.add(button_text)
                general_buttons.append(button)
            
            if general_buttons:
                print(f"🔘 Found {len(general_buttons)} general buttons")
                
                for button in general_buttons[:5]:  # Test max 5 buttons
                    try:
                        button_text = button.text.strip()
                        
                        print(f"   🔘 Testing button: {button_text}")
                        
                        before_shot = self.take_screenshot(f"button_before_{button_text}")
                        button.click()
                        time.sleep(1.5)
                        after_shot = self.take_screenshot(f"button_after_{button_text}")
                        
                        button_info = {
                            "name": button_text,
                            "type": ElementType.BUTTON.value,
                            "screenshots": [before_shot, after_shot]
                        }
                        
                        self.report["ui_elements"].append(button_info)
                        self.report["elements_tested"] += 1
                        
                        # Check for dialogs
                        dialogs = self.driver.find_elements(
                            By.CSS_SELECTOR,
                            ".dialog, .modal, .popup"
                        )
                        
                        if dialogs:
                            print(f"     💬 Dialog opened")
                            self.explore_dialog_briefly(f"Button: {button_text}", dialogs[0])
                        
                        # Close any open dialogs
                        self._close_all_menus()
                        
                    except Exception as e:
                        print(f"   ❌ Button failed: {str(e)}")
                    
                    time.sleep(1)
                    
        except Exception as e:
            print(f"⚠ Button exploration failed: {str(e)}")
    
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
            time.sleep(8)  # Give more time for image to load
            self.report["image_loaded"] = True
            print("🖼️ Image uploaded and loaded")
        
        # Initial screenshot
        self.take_screenshot("initial_state")
        
        return True
    
    def run_comprehensive_exploration(self):
        """Run comprehensive exploration of all UI elements"""
        print("\n" + "="*60)
        print("STARTING COMPREHENSIVE EXPLORATORY TESTING")
        print("="*60)
        print("🎯 GOAL: Explore ALL UI elements (Menus, Tools, Panels, etc.)")
        print("="*60 + "\n")
        
        try:
            # Setup
            if not self.setup_editor():
                return
            
            # 1. Explore Menu Bar (with dropdowns)
            self.explore_menu_bar()
            
            # 2. Explore Toolbar (with visual change detection)
            self.explore_toolbar()
            
            # 3. Explore Other UI Elements
            self.explore_other_ui_elements()
            
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
        
        # Count tools with visual changes
        tools_with_changes = sum(1 for t in self.report["tool_buttons"] if t.get("visual_change", False))
        tools_applied = sum(1 for t in self.report["tool_buttons"] if t.get("applied_to_image", False))
        
        self.report["summary"] = {
            "total_elements_tested": total_elements,
            "menu_items": total_menu_items,
            "tool_buttons": total_tools,
            "tools_applied": tools_applied,
            "tools_with_visual_changes": tools_with_changes,
            "ui_elements": total_ui_elements,
            "elements_passed": self.report["elements_passed"],
            "elements_failed": self.report["elements_failed"],
            "elements_tested": self.report["elements_tested"],
            "success_rate": f"{(self.report['elements_passed']/max(total_elements, 1)*100):.1f}%",
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
        print(f"   Tool Buttons: {total_tools}")
        print(f"   Tools Applied to Image: {tools_applied}")
        print(f"   Tools with Visual Changes: {tools_with_changes}")
        print(f"   UI Elements: {total_ui_elements}")
        print(f"   Passed: {self.report['elements_passed']}")
        print(f"   Failed: {self.report['elements_failed']}")
        print(f"   Success Rate: {self.report['summary']['success_rate']}")
        print(f"   Visual Change Rate: {self.report['summary']['visual_change_rate']}")
        print(f"   Effects Applied: {len(self.report['image_effects_applied'])}")
        print(f"   Issues Found: {len(self.report['issues_found'])}")
        print(f"   Duration: {self.report['test_duration']} seconds")
        print(f"\n📄 Full report saved to: {REPORT_PATH}")
        print(f"📸 Screenshots saved in: {SCREENSHOT_DIR}")
        
        # Print menu items tested
        if self.report["menu_items"]:
            print(f"\n📋 MENU ITEMS TESTED ({len(self.report['menu_items'])}):")
            for i, item in enumerate(self.report["menu_items"][:10], 1):
                has_dropdown = "✅" if item.get("opens_dropdown", False) else "❌"
                print(f"   {i}. {item['name']} (Dropdown: {has_dropdown})")
        
        # Print tools tested with visual change status
        if self.report["tool_buttons"]:
            print(f"\n🔧 TOOLS TESTED ({len(self.report['tool_buttons'])}):")
            for i, tool in enumerate(self.report["tool_buttons"][:15], 1):
                applied = "✅" if tool.get("applied_to_image", False) else "❌"
                visual = "✨" if tool.get("visual_change", False) else "⚫"
                print(f"   {i}. {applied}{visual} {tool['title']}")
    
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
        tester.run_comprehensive_exploration()
    except KeyboardInterrupt:
        print("\n\n🛑 Testing interrupted by user")
        tester.generate_final_report()
        tester.cleanup()
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        tester.cleanup()
        raise