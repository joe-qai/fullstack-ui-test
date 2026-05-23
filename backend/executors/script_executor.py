import os
import subprocess
import sys
import json
import time
import threading
from datetime import datetime, timezone
from typing import Dict, Any, Callable, Optional
from sqlalchemy.orm import Session
from executors.base_executor import BaseExecutor
from models.test_case import TestCase
from models.device import Device
from models.project import Project
from models.script import Script


class ScriptExecutor(BaseExecutor):
    """Script test executor using subprocess with start/wait lifecycle."""

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
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "message": message,
        }
        self.logs.append(entry)
        print(f"[{entry['timestamp']}] [{level}] {message}")
        return entry

    def _build_env(self, device: Device, project: Project = None) -> dict:
        env = os.environ.copy()
        env["DEVICE_SERIAL"] = device.serial
        if project and project.app_id:
            env["APP_PACKAGE"] = project.app_id
        return env

    def _parse_stderr_error(self, stderr: str) -> Optional[str]:
        import re
        match = re.search(r"ModuleNotFoundError: No module named ['\"](\w+)['\"]", stderr)
        if match:
            missing_module = match.group(1)
            self._log(f"Detected missing module: {missing_module}", "ERROR")
            return f"{missing_module}\u672a\u5b89\u88c5\uff01"
        return None

    def start(self, script: Script, device: Device, project: Project = None) -> subprocess.Popen:
        """Start script execution and return the Popen process immediately."""
        self._start_time = time.time()
        self.logs = []
        self.stdout_data = []
        self.stderr_data = []

        script_path = script.file_path
        self._log(f"Script Path: {script_path}", "INFO")

        if not os.path.exists(script_path):
            raise FileNotFoundError(f"Script file not found: {script_path}")

        env = self._build_env(device, project)
        self._log(f"Device Serial: {device.serial}", "INFO")
        if "APP_PACKAGE" in env:
            self._log(f"APP_PACKAGE: {env['APP_PACKAGE']}", "INFO")

        command = [sys.executable, script_path]
        self._log(f"Command: {' '.join(command)}", "INFO")
        self._log(f"Working directory: {os.path.dirname(script_path)}", "INFO")

        self.process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            cwd=os.path.dirname(script_path),
        )
        self._log(f"Process started (PID: {self.process.pid})", "INFO")
        return self.process

    def wait(self, cancel_check: Callable[[], bool] = lambda: False) -> Dict:
        """Wait for process completion, reading output line-by-line with cancellation support."""
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
            result["start_time"] = datetime.now(timezone.utc).isoformat()
            self._log("========== Script Execution Started ==========", "INFO")
            self._log("Waiting for script to complete...", "INFO")

            stderr_lines = []

            def read_stderr():
                for line in self.process.stderr:
                    stderr_lines.append(line)

            stderr_thread = threading.Thread(target=read_stderr, daemon=True)
            stderr_thread.start()

            stdout_lines = []
            cancelled = False

            while True:
                if cancel_check():
                    self._log("Cancellation requested, killing process...", "WARNING")
                    self.process.kill()
                    cancelled = True
                    break

                line = self.process.stdout.readline()
                if not line:
                    if self.process.poll() is not None:
                        break
                    continue

                stdout_lines.append(line)
                self._log(line.rstrip("\n\r"), "STDOUT")

            stderr_thread.join(timeout=2)
            stderr = "".join(stderr_lines)
            stdout = "".join(stdout_lines)

            self.process.wait()
            exit_code = self.process.returncode
            self._log(f"Script execution completed. Exit code: {exit_code}", "INFO")

            result["stdout"] = stdout
            result["stderr"] = stderr
            result["exit_code"] = exit_code

            if stderr:
                self._log("========== Script Output (STDERR) ==========", "INFO")
                for line in stderr.strip().split("\n"):
                    if line.strip():
                        self._log(line, "STDERR")

            if cancelled:
                result["status"] = "cancelled"
                self._log("Script execution was cancelled", "WARNING")
            elif exit_code == 0:
                result["status"] = "success"
                self._log("Script executed successfully", "INFO")
            else:
                result["status"] = "failed"
                self._log(f"Script failed with exit code {exit_code}", "ERROR")
                if stderr:
                    self._log(f"Error details: {stderr[:500]}...", "ERROR")
                    error = self._parse_stderr_error(stderr)
                    if error:
                        result["error"] = error

            result["end_time"] = datetime.now(timezone.utc).isoformat()
            result["duration_ms"] = int((time.time() - self._start_time) * 1000)
            self._log(f"Total execution time: {result['duration_ms']} ms", "INFO")
            self._log(f"========== Script Execution Completed ({result['status'].upper()}) ==========", "INFO")

            result["logs"] = self.logs

        except Exception as e:
            result["status"] = "cancelled" if cancel_check() else "failed"
            result["error"] = str(e)
            result["end_time"] = datetime.now(timezone.utc).isoformat()
            if self._start_time:
                result["duration_ms"] = int((time.time() - self._start_time) * 1000)
            self._log(f"EXCEPTION: {result['error']}", "ERROR")
            import traceback
            self._log(f"Traceback: {traceback.format_exc()}", "ERROR")

        return result

    def run_script(self, script: Script, device: Device, project: Project = None) -> Dict:
        """Execute a Script object directly (start + wait, no cancellation)."""
        self.start(script, device, project)
        return self.wait()

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
            self._start_time = time.time()
            result["start_time"] = datetime.now(timezone.utc).isoformat()
            self._log(f"========== Script Case Execution Started ==========", "INFO")
            self._log(f"Test Case ID: {test_case.id}", "INFO")
            self._log(f"Device Serial: {device.serial}", "INFO")
            self._log(f"Project: {project.name if project else 'None'}", "INFO")

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

            self.start(script, device, project)
            return self.wait()

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
        return {
            "serial": device.serial,
            "platform": device.platform,
            "status": device.status,
        }
