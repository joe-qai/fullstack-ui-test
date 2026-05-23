import os
import time
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from executors.base_executor import BaseExecutor
from models.test_case import TestCase
from models.device import Device
from models.project import Project
from models.element import Element
from models.keyword import Keyword

class AndroidExecutor(BaseExecutor):
    """Android test executor using uiautomator2."""

    def __init__(self):
        self.d = None
        self.current_step = 0
        self.logs = []
        self.screenshots = []
        self.last_error = None

    def _log(self, message: str, level: str = "INFO"):
        """Add a log entry."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "message": message,
            "step": self.current_step,
        }
        self.logs.append(entry)
        return entry

    def _take_screenshot(self, prefix: str = "") -> str:
        """Take a screenshot and save it."""
        try:
            screenshot_path = f"reports/screenshot_{prefix}_{int(time.time())}.png"
            if self.d:
                self.d.screenshot(screenshot_path)
                self.screenshots.append(screenshot_path)
                return screenshot_path
        except Exception as e:
            self._log(f"Screenshot failed: {e}", "ERROR")
        return ""

    def _get_element_locator(self, element_id: str, db: Session):
        """Get element locator from database."""
        element = db.query(Element).filter(Element.id == element_id).first()
        if not element:
            return None
        return {
            "type": element.locator_type,
            "value": element.locator_value,
        }

    def _find_element(self, d, locator: Dict):
        """Find element using uiautomator2.
        
        Supported locator types:
        - text: 精确匹配文本
        - textContains: 包含匹配文本
        - resourceId: 资源ID
        - xpath: XPath路径
        - className: 类名
        - description: 精确匹配描述
        - descriptionContains: 包含匹配描述
        """
        locator_type = locator["type"]
        locator_value = locator["value"]

        if locator_type in ("resource-id", "resourceId"):
            return d(resourceId=locator_value)
        elif locator_type == "xpath":
            return d.xpath(locator_value)
        elif locator_type == "text":
            return d(text=locator_value)
        elif locator_type == "textContains":
            return d(textContains=locator_value)
        elif locator_type in ("className", "class"):
            return d(className=locator_value)
        elif locator_type == "description":
            return d(description=locator_value)
        elif locator_type == "descriptionContains":
            return d(descriptionContains=locator_value)
        else:
            raise ValueError(f"Unknown locator type: {locator_type}")

    def _execute_keyword(self, d, keyword_name: str, locator: Optional[Dict], params: Dict) -> bool:
        """Execute a single keyword."""
        try:
            if keyword_name == "click":
                element = self._find_element(d, locator)
                timeout = params.get("timeout", 10)
                element.wait(timeout=timeout)
                element.click()

            elif keyword_name == "input":
                element = self._find_element(d, locator)
                timeout = params.get("timeout", 10)
                element.wait(timeout=timeout)
                text = params.get("text", "")
                element.set_text(text)

            elif keyword_name == "swipe":
                direction = params.get("direction", "up")
                if direction == "up":
                    d.swipe(0.5, 0.8, 0.5, 0.2)
                elif direction == "down":
                    d.swipe(0.5, 0.2, 0.5, 0.8)
                elif direction == "left":
                    d.swipe(0.8, 0.5, 0.2, 0.5)
                elif direction == "right":
                    d.swipe(0.2, 0.5, 0.8, 0.5)

            elif keyword_name == "wait_element":
                element = self._find_element(d, locator)
                timeout = params.get("timeout", 10)
                element.wait(timeout=timeout)

            elif keyword_name == "assert_element_exists":
                element = self._find_element(d, locator)
                timeout = params.get("timeout", 10)
                if not element.wait(timeout=timeout):
                    raise AssertionError(f"Element does not exist (waited {timeout}s)")
                self._log(f"Assertion passed: element exists after {timeout}s", "INFO")

            elif keyword_name == "assert_element_not_exists":
                element = self._find_element(d, locator)
                timeout = params.get("timeout", 10)
                if element.wait(timeout=timeout):
                    raise AssertionError(f"Element should not exist but it does")
                self._log("Assertion passed: element does not exist", "INFO")

            elif keyword_name == "assert_element_visible":
                element = self._find_element(d, locator)
                timeout = params.get("timeout", 10)
                if not element.wait(timeout=timeout):
                    raise AssertionError(f"Element is not visible (waited {timeout}s)")
                if not element.info.get("visible", True):
                    raise AssertionError("Element is not visible")
                self._log("Assertion passed: element is visible", "INFO")

            elif keyword_name == "assert_element_not_visible":
                element = self._find_element(d, locator)
                timeout = params.get("timeout", 10)
                if element.wait(timeout=timeout):
                    if element.info.get("visible", True):
                        raise AssertionError("Element should not be visible but it is")
                self._log("Assertion passed: element is not visible", "INFO")

            elif keyword_name == "assert_element_enabled":
                element = self._find_element(d, locator)
                timeout = params.get("timeout", 10)
                if not element.wait(timeout=timeout):
                    raise AssertionError(f"Element is not enabled (waited {timeout}s)")
                if not element.info.get("enabled", True):
                    raise AssertionError("Element is not enabled")
                self._log("Assertion passed: element is enabled", "INFO")

            elif keyword_name == "assert_element_disabled":
                element = self._find_element(d, locator)
                timeout = params.get("timeout", 10)
                if element.wait(timeout=timeout):
                    if element.info.get("enabled", True):
                        raise AssertionError("Element should be disabled but it is enabled")
                self._log("Assertion passed: element is disabled", "INFO")

            elif keyword_name == "assert_text_equals":
                element = self._find_element(d, locator)
                timeout = params.get("timeout", 10)
                if not element.wait(timeout=timeout):
                    raise AssertionError(f"Element not found for text assertion (waited {timeout}s)")
                actual = element.get_text()
                expected = params.get("expected", "")
                assert actual == expected, f"Text mismatch: expected '{expected}', got '{actual}'"
                self._log(f"Assertion passed: text equals '{expected}'", "INFO")

            elif keyword_name == "assert_text_contains":
                element = self._find_element(d, locator)
                timeout = params.get("timeout", 10)
                if not element.wait(timeout=timeout):
                    raise AssertionError(f"Element not found for text assertion (waited {timeout}s)")
                actual = element.get_text()
                expected = params.get("expected", "")
                assert expected in actual, f"Text '{expected}' not found in '{actual}'"
                self._log(f"Assertion passed: text contains '{expected}'", "INFO")

            elif keyword_name == "assert_text_on_screen":
                target = params.get("text", "")
                timeout = params.get("timeout", 10)
                if not d(text=target).wait(timeout=timeout):
                    raise AssertionError(f"Text '{target}' not found on screen (waited {timeout}s)")
                self._log(f"Assertion passed: text '{target}' found on screen", "INFO")

            elif keyword_name == "assert_text_not_on_screen":
                target = params.get("text", "")
                timeout = params.get("timeout", 10)
                if d(text=target).wait(timeout=timeout):
                    raise AssertionError(f"Text '{target}' should not be on screen but it is")
                self._log(f"Assertion passed: text '{target}' not on screen", "INFO")

            elif keyword_name == "press_back":
                d.press("back")

            elif keyword_name == "press_home":
                d.press("home")

            elif keyword_name == "scroll_to":
                text = params.get("text", "")
                d(text=text).scroll_to()

            elif keyword_name in ("launch_app", "start_app"):
                package = params.get("package", "")
                d.app_start(package)

            elif keyword_name == "sleep":
                seconds = float(params.get("seconds", 1))
                import time
                time.sleep(seconds)

            elif keyword_name == "stop_app":
                package = params.get("package", "")
                d.app_stop(package)

            elif keyword_name == "adb_shell":
                import subprocess
                cmd = params.get("command", "")
                r = d.shell(cmd)
                self._log(f"adb shell: {cmd} -> {r}", "INFO")

            elif keyword_name == "get_packages":
                filter_str = params.get("filter", "")
                packages = d.app_list()
                if filter_str:
                    packages = [p for p in packages if filter_str in p]
                self._log(f"Packages: {packages}", "INFO")

            elif keyword_name == "get_screenshot":
                path = self._take_screenshot("manual")
                self._log(f"Screenshot saved: {path}", "INFO")

            elif keyword_name == "wait_and_click":
                element = self._find_element(d, locator)
                timeout = params.get("timeout", 10)
                if element.wait(timeout=timeout):
                    element.click()
                else:
                    raise TimeoutError(f"Element not visible after {timeout}s")

            elif keyword_name == "find_text":
                target = params.get("text", "")
                found = d(text=target)
                if found.exists:
                    bounds = found.info.get("bounds", {})
                    self._log(f"Found text '{target}' at {bounds}", "INFO")
                else:
                    raise AssertionError(f"Text '{target}' not found on screen")

            elif keyword_name == "long_click":
                element = self._find_element(d, locator)
                timeout = params.get("timeout", 10)
                element.wait(timeout=timeout)
                duration = params.get("duration", 2000)
                element.long_click(duration=duration)

            elif keyword_name == "clear_text":
                element = self._find_element(d, locator)
                timeout = params.get("timeout", 10)
                element.wait(timeout=timeout)
                element.clear_text()

            elif keyword_name == "get_text":
                element = self._find_element(d, locator)
                timeout = params.get("timeout", 10)
                element.wait(timeout=timeout)
                text = element.get_text()
                self._log(f"Element text: {text}", "INFO")

            elif keyword_name == "press_keycode":
                keycode = params.get("keycode", 4)
                d.press(keycode)

            elif keyword_name == "set_orientation":
                orientation = params.get("orientation", "portrait")
                d.freeze_rotation(orientation == "landscape")
                d.set_orientation(orientation)

            elif keyword_name == "open_notification":
                d.open_notification()

            elif keyword_name == "get_page_source":
                source = d.dump_hierarchy()
                self._log(f"Page source length: {len(source)}", "INFO")

            elif keyword_name == "ocr":
                try:
                    from PIL import Image
                    import pytesseract
                    path = self._take_screenshot("ocr")
                    if path:
                        text = pytesseract.image_to_string(Image.open(path), lang='chi_sim+eng')
                        self._log(f"OCR: {text[:200]}", "INFO")
                except ImportError:
                    self._log("OCR requires Pillow+pytesseract", "ERROR")

            elif keyword_name == "wait_for_text":
                target = params.get("text", "")
                timeout = params.get("timeout", 10)
                d(text=target).wait(timeout=timeout)

            elif keyword_name == "drag_and_drop":
                element = self._find_element(d, locator)
                timeout = params.get("timeout", 10)
                element.wait(timeout=timeout)
                end_x = params.get("end_x", 0)
                end_y = params.get("end_y", 0)
                element.drag(end_x, end_y)

            elif keyword_name == "reboot_device":
                self._log("Rebooting device...", "WARNING")
                d.shell("reboot")

            elif keyword_name == "take_bugreport":
                result = d.shell("bugreportz")
                self._log(f"Bugreport: {result}", "INFO")

            elif keyword_name == "get_battery_info":
                info = d.shell("dumpsys battery")
                self._log(f"Battery info:\n{info}", "INFO")

            elif keyword_name == "clear_app_data":
                pkg = params.get("package", "")
                d.app_clear(pkg)
                self._log(f"Cleared app data for {pkg}", "INFO")

            elif keyword_name == "kill_app":
                pkg = params.get("package", "")
                d.app_stop(pkg)
                self._log(f"Force stopped {pkg}", "INFO")

            elif keyword_name == "get_current_activity":
                current = d.app_current()
                self._log(f"Current activity: {current}", "INFO")

            elif keyword_name == "get_device_info":
                info = d.device_info
                self._log(f"Device info: {info}", "INFO")

            else:
                # Try custom keyword
                from core.custom_keyword_loader import load_custom_keyword_function
                custom_func = load_custom_keyword_function(keyword_name)
                if custom_func:
                    try:
                        element = None
                        if locator:
                            element = self._find_element(d, locator)
                        custom_func(d, element, params)
                        return True
                    except Exception as e:
                        self._log(f"Custom keyword {keyword_name} failed: {e}", "ERROR")
                        return False
                self._log(f"Unknown keyword: {keyword_name}", "ERROR")
                return False

            return True

        except Exception as e:
            self.last_error = str(e)
            self._log(f"Keyword execution failed: {e}", "ERROR")
            return False

    def run(self, test_case: TestCase, device: Device, project: Project = None, db: Session = None) -> Dict:
        """Execute test case on Android device."""
        import uiautomator2 as u2

        result = {
            "status": "pending",
            "steps": [],
            "logs": [],
            "screenshots": [],
            "error": None,
            "device_info": {},
        }

        try:
            # 1. Connect to device
            self._log(f"Connecting to device {device.serial}...")
            self.d = u2.connect(device.serial)

            # 2. Get device info
            device_info = self.d.device_info
            result["device_info"] = {
                "serial": device.serial,
                "model": device_info.get("model", "unknown"),
                "version": device_info.get("version", "unknown"),
                "screen": device_info.get("display", {}),
            }

            # 3. Launch app if project specified
            if project and project.app_id:
                self._log(f"Launching app {project.app_id}...")
                self.d.app_start(project.app_id)
                time.sleep(2)

            # 4. Execute steps
            for i, step in enumerate(test_case.steps):
                self.current_step = i + 1

                # Resolve keyword name from ID
                kw_name = step.keyword_id
                if db:
                    kw = db.query(Keyword).filter(Keyword.id == step.keyword_id).first()
                    if kw:
                        kw_name = kw.name

                step_result = {
                    "order": step.step_order,
                    "keyword": kw_name,
                    "status": "pending",
                    "screenshot": "",
                    "error": None,
                }

                try:
                    # Get element locator
                    locator = None
                    if step.po_element_id and db:
                        locator = self._get_element_locator(step.po_element_id, db)

                    # Parse params
                    params = {}
                    if step.params:
                        params = json.loads(step.params)

                    # Execute keyword
                    self.last_error = None
                    success = self._execute_keyword(self.d, kw_name, locator, params)

                    if success:
                        step_result["status"] = "success"
                        self._log(f"Step {step.step_order}: {kw_name} - SUCCESS")
                    else:
                        step_result["status"] = "failed"
                        step_result["error"] = self.last_error or f"Keyword {kw_name} failed"
                        self._log(f"Step {step.step_order}: {kw_name} - FAILED: {step_result['error']}", "ERROR")

                    # Take screenshot
                    screenshot_path = self._take_screenshot(f"step_{step.step_order}")
                    step_result["screenshot"] = screenshot_path

                except Exception as e:
                    step_result["status"] = "failed"
                    step_result["error"] = str(e)
                    self._log(f"Step {step.step_order} error: {e}", "ERROR")

                    # Take error screenshot
                    screenshot_path = self._take_screenshot(f"error_step_{step.step_order}")
                    step_result["screenshot"] = screenshot_path

                result["steps"].append(step_result)

                # Stop execution if current step failed
                if step_result["status"] == "failed":
                    self._log(f"Test stopped at step {step.step_order} due to failure", "WARNING")
                    break

            # 5. Determine overall status
            failed_steps = [s for s in result["steps"] if s["status"] == "failed"]
            if failed_steps:
                result["status"] = "failed"
            else:
                result["status"] = "success"

            result["logs"] = self.logs
            result["screenshots"] = self.screenshots

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            self._log(f"Test execution failed: {e}", "ERROR")

        finally:
            # Cleanup
            if self.d:
                try:
                    self.d.service("uiautomator").stop()
                except:
                    pass
                self.d = None

        return result

    def get_device_info(self, device: Device) -> Dict:
        """Get Android device information."""
        import uiautomator2 as u2
        try:
            d = u2.connect(device.serial)
            info = d.device_info
            return {
                "serial": device.serial,
                "model": info.get("model", "unknown"),
                "version": info.get("version", "unknown"),
                "screen": info.get("display", {}),
            }
        except Exception as e:
            return {
                "serial": device.serial,
                "error": str(e),
            }
