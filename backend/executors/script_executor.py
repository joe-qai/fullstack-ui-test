import os
import subprocess
import sys
import json
import time
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
        self._start_time = None

    @property
    def running_process(self):
        return self.process

    def _log(self, message: str, level: str = "INFO"):
        """Add a log entry."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "message": message,
        }
        self.logs.append(entry)
        # Also print to console for debugging
        print(f"[{entry['timestamp']}] [{level}] {message}")
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
            "start_time": None,
            "end_time": None,
            "duration_ms": None,
        }

        try:
            # Record start time
            self._start_time = time.time()
            result["start_time"] = datetime.now(timezone.utc).isoformat()
            self._log(f"========== Script Execution Started ==========", "INFO")
            self._log(f"Test Case ID: {test_case.id}", "INFO")
            self._log(f"Device Serial: {device.serial}", "INFO")
            self._log(f"Project: {project.name if project else 'None'}", "INFO")

            # 1. Get script file path
            if not test_case.script_id or not db:
                result["status"] = "failed"
                result["error"] = "No script associated with this test case"
                self._log(f"ERROR: {result['error']}", "ERROR")
                return result

            script = db.query(Script).filter(Script.id == test_case.script_id).first()
            if not script:
                result["status"] = "failed"
                result["error"] = f"Script {test_case.script_id} not found"
                self._log(f"ERROR: {result['error']}", "ERROR")
                return result

            script_path = script.file_path
            self._log(f"Script Path: {script_path}", "INFO")
            
            if not os.path.exists(script_path):
                result["status"] = "failed"
                result["error"] = f"Script file not found: {script_path}"
                self._log(f"ERROR: {result['error']}", "ERROR")
                return result

            # 2. Build environment
            env = os.environ.copy()
            env["DEVICE_SERIAL"] = device.serial
            if project and project.app_id:
                env["APP_PACKAGE"] = project.app_id
            
            self._log(f"Environment Variables:", "INFO")
            self._log(f"  DEVICE_SERIAL: {env['DEVICE_SERIAL']}", "INFO")
            if "APP_PACKAGE" in env:
                self._log(f"  APP_PACKAGE: {env['APP_PACKAGE']}", "INFO")

            # 3. Prepare command
            command = [sys.executable, script_path]
            self._log(f"Command to execute: {' '.join(command)}", "INFO")
            self._log(f"Working directory: {os.path.dirname(script_path)}", "INFO")
            self._log(f"Python executable: {sys.executable}", "INFO")

            # 4. Execute script
            self._log(f"Starting script execution...", "INFO")

            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                cwd=os.path.dirname(script_path),
            )

            # 5. Capture output
            self._log("Waiting for script to complete...", "INFO")
            stdout, stderr = self.process.communicate()
            self._log(f"Script execution completed. Exit code: {self.process.returncode}", "INFO")
            
            result["stdout"] = stdout
            result["stderr"] = stderr
            result["exit_code"] = self.process.returncode

            # 6. Parse logs
            self._log(f"========== Script Output (STDOUT) ==========", "INFO")
            if stdout:
                for line in stdout.strip().split("\n"):
                    if line.strip():
                        self._log(line, "STDOUT")
            else:
                self._log("(empty)", "STDOUT")
            
            if stderr:
                self._log(f"========== Script Output (STDERR) ==========", "INFO")
                for line in stderr.strip().split("\n"):
                    if line.strip():
                        self._log(line, "STDERR")

            # 7. Determine status
            if self.process.returncode == 0:
                result["status"] = "success"
                self._log("Script executed successfully", "INFO")
            else:
                result["status"] = "failed"
                self._log(f"Script failed with exit code {self.process.returncode}", "ERROR")
                if stderr:
                    self._log(f"Error details from stderr: {stderr[:500]}...", "ERROR")
                    # 解析 ModuleNotFoundError，提取缺失的包名
                    import re
                    match = re.search(r"ModuleNotFoundError: No module named ['\"](\w+)['\"]", stderr)
                    if match:
                        missing_module = match.group(1)
                        result["error"] = f"{missing_module}未安装！"
                        self._log(f"Detected missing module: {missing_module}", "ERROR")

            # Record end time and duration
            result["end_time"] = datetime.now(timezone.utc).isoformat()
            result["duration_ms"] = int((time.time() - self._start_time) * 1000)
            self._log(f"Total execution time: {result['duration_ms']} ms", "INFO")
            self._log(f"========== Script Execution Completed ({result['status'].upper()}) ==========", "INFO")

            result["logs"] = self.logs

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            result["end_time"] = datetime.now(timezone.utc).isoformat()
            if self._start_time:
                result["duration_ms"] = int((time.time() - self._start_time) * 1000)
            self._log(f"EXCEPTION: {result['error']}", "ERROR")
            import traceback
            self._log(f"Traceback: {traceback.format_exc()}", "ERROR")

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
            "start_time": None,
            "end_time": None,
            "duration_ms": None,
        }

        try:
            # Record start time
            self._start_time = time.time()
            result["start_time"] = datetime.now(timezone.utc).isoformat()
            self._log(f"========== Direct Script Execution Started ==========", "INFO")
            self._log(f"Script ID: {script.id}", "INFO")
            self._log(f"Script Name: {script.name}", "INFO")
            self._log(f"Device Serial: {device.serial}", "INFO")
            self._log(f"Project: {project.name if project else 'None'}", "INFO")

            # 1. Get script file path
            script_path = script.file_path
            self._log(f"Script Path: {script_path}", "INFO")
            
            if not os.path.exists(script_path):
                result["status"] = "failed"
                result["error"] = f"Script file not found: {script_path}"
                self._log(f"ERROR: {result['error']}", "ERROR")
                return result

            # 2. Build environment
            env = os.environ.copy()
            env["DEVICE_SERIAL"] = device.serial
            if project and project.app_id:
                env["APP_PACKAGE"] = project.app_id
            
            self._log(f"Environment Variables:", "INFO")
            self._log(f"  DEVICE_SERIAL: {env['DEVICE_SERIAL']}", "INFO")
            if "APP_PACKAGE" in env:
                self._log(f"  APP_PACKAGE: {env['APP_PACKAGE']}", "INFO")

            # 3. Prepare command
            command = [sys.executable, script_path]
            self._log(f"Command to execute: {' '.join(command)}", "INFO")
            self._log(f"Working directory: {os.path.dirname(script_path)}", "INFO")
            self._log(f"Python executable: {sys.executable}", "INFO")

            # 4. Execute script
            self._log(f"Starting script execution...", "INFO")

            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                cwd=os.path.dirname(script_path),
            )

            # 5. Capture output
            self._log("Waiting for script to complete...", "INFO")
            stdout, stderr = self.process.communicate()
            self._log(f"Script execution completed. Exit code: {self.process.returncode}", "INFO")
            
            result["stdout"] = stdout
            result["stderr"] = stderr
            result["exit_code"] = self.process.returncode

            # 6. Parse logs
            self._log(f"========== Script Output (STDOUT) ==========", "INFO")
            if stdout:
                for line in stdout.strip().split("\n"):
                    if line.strip():
                        self._log(line, "STDOUT")
            else:
                self._log("(empty)", "STDOUT")
            
            if stderr:
                self._log(f"========== Script Output (STDERR) ==========", "INFO")
                for line in stderr.strip().split("\n"):
                    if line.strip():
                        self._log(line, "STDERR")

            # 7. Determine status
            if self.process.returncode == 0:
                result["status"] = "success"
                self._log("Script executed successfully", "INFO")
            else:
                result["status"] = "failed"
                self._log(f"Script failed with exit code {self.process.returncode}", "ERROR")
                if stderr:
                    self._log(f"Error details from stderr: {stderr[:500]}...", "ERROR")
                    # 解析 ModuleNotFoundError，提取缺失的包名
                    import re
                    match = re.search(r"ModuleNotFoundError: No module named ['\"](\w+)['\"]", stderr)
                    if match:
                        missing_module = match.group(1)
                        result["error"] = f"{missing_module}未安装！"
                        self._log(f"Detected missing module: {missing_module}", "ERROR")

            # Record end time and duration
            result["end_time"] = datetime.now(timezone.utc).isoformat()
            result["duration_ms"] = int((time.time() - self._start_time) * 1000)
            self._log(f"Total execution time: {result['duration_ms']} ms", "INFO")
            self._log(f"========== Script Execution Completed ({result['status'].upper()}) ==========", "INFO")

            result["logs"] = self.logs

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            result["end_time"] = datetime.now(timezone.utc).isoformat()
            if self._start_time:
                result["duration_ms"] = int((time.time() - self._start_time) * 1000)
            self._log(f"EXCEPTION: {result['error']}", "ERROR")
            import traceback
            self._log(f"Traceback: {traceback.format_exc()}", "ERROR")

        return result

    def get_device_info(self, device: Device) -> Dict:
        """Get device information for script execution."""
        return {
            "serial": device.serial,
            "platform": device.platform,
            "status": device.status,
        }
