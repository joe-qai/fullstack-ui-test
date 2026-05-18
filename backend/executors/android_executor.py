import os
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from executors.base_executor import BaseExecutor
from models.test_case import TestCase
from models.device import Device
from models.project import Project
from models.element import Element

class AndroidExecutor(BaseExecutor):
    """Android test executor using uiautomator2."""

    def __init__(self):
        self.d = None
        self.current_step = 0
        self.logs = []
        self.screenshots = []

    def _log(self, message: str, level: str = "INFO"):
        """Add a log entry."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
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
        """Find element using uiautomator2."""
        locator_type = locator["type"]
        locator_value = locator["value"]

        if locator_type == "resource-id":
            return d(resourceId=locator_value)
        elif locator_type == "xpath":
            return d.xpath(locator_value)
        elif locator_type == "text":
            return d(text=locator_value)
        elif locator_type == "class":
            return d(className=locator_value)
        else:
            raise ValueError(f"Unknown locator type: {locator_type}")

    def _execute_keyword(self, d, keyword_name: str, locator: Optional[Dict], params: Dict) -> bool:
        """Execute a single keyword."""
        try:
            if keyword_name == "click":
                element = self._find_element(d, locator)
                element.click()

            elif keyword_name == "input":
                element = self._find_element(d, locator)
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
                assert element.exists, "Element does not exist"

            elif keyword_name == "press_back":
                d.press("back")

            elif keyword_name == "press_home":
                d.press("home")

            elif keyword_name == "scroll_to":
                text = params.get("text", "")
                d(text=text).scroll_to()

            elif keyword_name == "launch_app":
                package = params.get("package", "")
                d.app_start(package)

            elif keyword_name == "stop_app":
                package = params.get("package", "")
                d.app_stop(package)

            else:
                self._log(f"Unknown keyword: {keyword_name}", "ERROR")
                return False

            return True

        except Exception as e:
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
                step_result = {
                    "order": step.step_order,
                    "keyword": step.keyword_id,
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
                    success = self._execute_keyword(self.d, step.keyword_id, locator, params)

                    if success:
                        step_result["status"] = "success"
                        self._log(f"Step {step.step_order}: {step.keyword_id} - SUCCESS")
                    else:
                        step_result["status"] = "failed"
                        step_result["error"] = f"Keyword {step.keyword_id} failed"
                        self._log(f"Step {step.step_order}: {step.keyword_id} - FAILED", "ERROR")

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
