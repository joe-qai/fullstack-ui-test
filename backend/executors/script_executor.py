import os
import subprocess
import json
from datetime import datetime, timezone
from typing import Dict, Any
from sqlalchemy.orm import Session
from executors.base_executor import BaseExecutor
from models.test_case import TestCase
from models.device import Device
from models.project import Project
from models.script import Script

class ScriptExecutor(BaseExecutor):
    """Script test executor using subprocess."""

    def __init__(self):
        self.process = None
        self.logs = []
        self.stdout_data = []
        self.stderr_data = []

    def _log(self, message: str, level: str = "INFO"):
        """Add a log entry."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "message": message,
        }
        self.logs.append(entry)
        return entry

    def run(self, test_case: TestCase, device: Device, project: Project = None, db: Session = None) -> Dict:
        """Execute a script-based test case."""
        result = {
            "status": "pending",
            "logs": [],
            "stdout": "",
            "stderr": "",
            "exit_code": None,
            "error": None,
        }

        try:
            # 1. Get script file path
            if not test_case.script_id or not db:
                result["status"] = "failed"
                result["error"] = "No script associated with this test case"
                return result

            script = db.query(Script).filter(Script.id == test_case.script_id).first()
            if not script:
                result["status"] = "failed"
                result["error"] = f"Script {test_case.script_id} not found"
                return result

            script_path = script.file_path
            if not os.path.exists(script_path):
                result["status"] = "failed"
                result["error"] = f"Script file not found: {script_path}"
                return result

            # 2. Build environment
            env = os.environ.copy()
            env["DEVICE_SERIAL"] = device.serial
            if project and project.app_id:
                env["APP_PACKAGE"] = project.app_id

            # 3. Execute script
            self._log(f"Executing script: {script_path} on device {device.serial}")

            self.process = subprocess.Popen(
                ["python", script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                cwd=os.path.dirname(script_path),
            )

            # 4. Capture output
            stdout, stderr = self.process.communicate()
            result["stdout"] = stdout
            result["stderr"] = stderr
            result["exit_code"] = self.process.returncode

            # 5. Parse logs
            if stdout:
                for line in stdout.strip().split("\n"):
                    self._log(line, "INFO")
            if stderr:
                for line in stderr.strip().split("\n"):
                    self._log(line, "ERROR")

            # 6. Determine status
            if self.process.returncode == 0:
                result["status"] = "success"
                self._log("Script executed successfully", "INFO")
            else:
                result["status"] = "failed"
                self._log(f"Script failed with exit code {self.process.returncode}", "ERROR")

            result["logs"] = self.logs

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            self._log(f"Script execution failed: {e}", "ERROR")

        return result

    def run_script(self, script: Script, device: Device, project: Project = None) -> Dict:
        """Execute a Script object directly (without a TestCase wrapper)."""
        result = {
            "status": "pending",
            "logs": [],
            "stdout": "",
            "stderr": "",
            "exit_code": None,
            "error": None,
        }

        try:
            # 1. Get script file path
            script_path = script.file_path
            if not os.path.exists(script_path):
                result["status"] = "failed"
                result["error"] = f"Script file not found: {script_path}"
                return result

            # 2. Build environment
            env = os.environ.copy()
            env["DEVICE_SERIAL"] = device.serial
            if project and project.app_id:
                env["APP_PACKAGE"] = project.app_id

            # 3. Execute script
            self._log(f"Executing script: {script_path} on device {device.serial}")

            self.process = subprocess.Popen(
                ["python", script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                cwd=os.path.dirname(script_path),
            )

            # 4. Capture output
            stdout, stderr = self.process.communicate()
            result["stdout"] = stdout
            result["stderr"] = stderr
            result["exit_code"] = self.process.returncode

            # 5. Parse logs
            if stdout:
                for line in stdout.strip().split("\n"):
                    self._log(line, "INFO")
            if stderr:
                for line in stderr.strip().split("\n"):
                    self._log(line, "ERROR")

            # 6. Determine status
            if self.process.returncode == 0:
                result["status"] = "success"
                self._log("Script executed successfully", "INFO")
            else:
                result["status"] = "failed"
                self._log(f"Script failed with exit code {self.process.returncode}", "ERROR")

            result["logs"] = self.logs

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            self._log(f"Script execution failed: {e}", "ERROR")

        return result

    def get_device_info(self, device: Device) -> Dict:
        """Get device information for script execution."""
        return {
            "serial": device.serial,
            "platform": device.platform,
            "status": device.status,
        }
