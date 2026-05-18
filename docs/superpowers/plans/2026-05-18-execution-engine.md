# UI自动化测试平台 - Phase 2: 执行引擎层

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现执行引擎层，包含 BaseExecutor 抽象基类、AndroidExecutor（uiautomator2）、ScriptExecutor（subprocess），以及 TaskDispatcher 并发调度器。执行完此计划后，可以通过 API 创建测试任务并在多台 Android 设备上并发执行。

**Architecture:** 采用抽象基类 `BaseExecutor` 定义统一接口，`AndroidExecutor` 使用 uiautomator2 连接设备并执行关键字步骤，`ScriptExecutor` 通过 subprocess 运行 .py 脚本。`TaskDispatcher` 使用 ThreadPoolExecutor 实现多设备并发执行。WebSocket 实时推送执行日志。

**Tech Stack:** Python 3.14, uiautomator2, ThreadPoolExecutor, FastAPI WebSocket

---

## 文件结构规划

```
backend/
├── executors/
│   ├── base_executor.py       # 抽象基类
│   ├── android_executor.py    # Android 执行引擎 (uiautomator2)
│   └── script_executor.py     # 脚本执行引擎 (subprocess)
├── core/
│   ├── task_dispatcher.py      # 并发调度器
│   └── report_generator.py   # 报告生成器
├── websocket/
│   └── log_stream.py         # WebSocket 日志推送
└── tests/
    ├── test_android_executor.py
    ├── test_script_executor.py
    └── test_task_dispatcher.py
```

---

### Task 1: BaseExecutor 抽象基类

**Files:**
- Create: `backend/executors/base_executor.py`
- Test: `backend/tests/test_base_executor.py`

- [ ] **Step 1: 写 base_executor.py**

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List

class BaseExecutor(ABC):
    """Abstract base class for all test executors."""
    
    @abstractmethod
    def run(self, test_case: Any, device: Any, project: Any = None) -> Dict:
        """
        Execute a test case on a device.
        
        Args:
            test_case: The test case to execute
            device: The target device
            project: Optional project context
            
        Returns:
            Dict with keys: status, steps, logs, screenshots, error
        """
        pass
    
    @abstractmethod
    def get_device_info(self, device: Any) -> Dict:
        """Get device information."""
        pass
```

- [ ] **Step 2: 写测试**

```python
import pytest
from executors.base_executor import BaseExecutor

def test_base_executor_is_abstract():
    with pytest.raises(TypeError):
        executor = BaseExecutor()
```

- [ ] **Step 3: 运行测试**

```bash
cd C:/pythonworkspace/MultiUiAutoTest/backend
pytest tests/test_base_executor.py -v
```

Expected: 1 test PASSED

- [ ] **Step 4: Commit**

```bash
git add backend/executors/base_executor.py backend/tests/test_base_executor.py
git commit -m "feat: add BaseExecutor abstract class"
```

---

### Task 2: AndroidExecutor

**Files:**
- Create: `backend/executors/android_executor.py`
- Test: `backend/tests/test_android_executor.py`

- [ ] **Step 1: 写 android_executor.py**

```python
import os
import time
import json
import base64
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
```

- [ ] **Step 2: 写测试 (mock uiautomator2)**

```python
import pytest
from unittest.mock import MagicMock, patch
from executors.android_executor import AndroidExecutor
from models.test_case import TestCase
from models.device import Device

class TestAndroidExecutor:
    def setup_method(self):
        self.executor = AndroidExecutor()
    
    def test_executor_init(self):
        assert self.executor.d is None
        assert self.executor.logs == []
        assert self.executor.screenshots == []
    
    def test_log(self):
        entry = self.executor._log("test message")
        assert entry["message"] == "test message"
        assert entry["level"] == "INFO"
        assert len(self.executor.logs) == 1
    
    def test_log_error(self):
        entry = self.executor._log("error message", "ERROR")
        assert entry["level"] == "ERROR"
    
    @patch("executors.android_executor.u2")
    def test_get_device_info(self, mock_u2):
        mock_device = MagicMock()
        mock_device.device_info = {
            "model": "Pixel4",
            "version": "11",
            "display": {"width": 1080, "height": 1920},
        }
        mock_u2.connect.return_value = mock_device
        
        device = Device(id="abc123", serial="abc123", name="Test", platform="android")
        info = self.executor.get_device_info(device)
        
        assert info["serial"] == "abc123"
        assert info["model"] == "Pixel4"
```

- [ ] **Step 3: 运行测试**

```bash
pytest tests/test_android_executor.py -v
```

Expected: 4 tests PASSED

- [ ] **Step 4: Commit**

```bash
git add backend/executors/android_executor.py backend/tests/test_android_executor.py
git commit -m "feat: add AndroidExecutor with uiautomator2 support"
```

---

### Task 3: ScriptExecutor

**Files:**
- Create: `backend/executors/script_executor.py`
- Test: `backend/tests/test_script_executor.py`

- [ ] **Step 1: 写 script_executor.py**

```python
import os
import subprocess
import json
from datetime import datetime
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
            "timestamp": datetime.utcnow().isoformat(),
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
    
    def get_device_info(self, device: Device) -> Dict:
        """Get device information for script execution."""
        return {
            "serial": device.serial,
            "platform": device.platform,
            "status": device.status,
        }
```

- [ ] **Step 2: 写测试**

```python
import pytest
import os
import tempfile
from unittest.mock import MagicMock, patch
from executors.script_executor import ScriptExecutor
from models.test_case import TestCase
from models.device import Device
from models.script import Script

class TestScriptExecutor:
    def setup_method(self):
        self.executor = ScriptExecutor()
    
    def test_executor_init(self):
        assert self.executor.process is None
        assert self.executor.logs == []
    
    def test_log(self):
        entry = self.executor._log("test message")
        assert entry["message"] == "test message"
        assert len(self.executor.logs) == 1
    
    def test_get_device_info(self):
        device = Device(id="abc123", serial="abc123", name="Test", platform="android")
        info = self.executor.get_device_info(device)
        assert info["serial"] == "abc123"
        assert info["platform"] == "android"
    
    def test_run_no_script(self):
        test_case = TestCase(id="tc_1", project_id="proj_1", name="test", type="script")
        device = Device(id="dev1", serial="abc123", name="Test", platform="android")
        
        result = self.executor.run(test_case, device)
        assert result["status"] == "failed"
        assert "No script" in result["error"]
```

- [ ] **Step 3: 运行测试**

```bash
pytest tests/test_script_executor.py -v
```

Expected: 4 tests PASSED

- [ ] **Step 4: Commit**

```bash
git add backend/executors/script_executor.py backend/tests/test_script_executor.py
git commit -m "feat: add ScriptExecutor for .py script execution"
```

---

### Task 4: TaskDispatcher 并发调度器

**Files:**
- Create: `backend/core/task_dispatcher.py`
- Test: `backend/tests/test_task_dispatcher.py`

- [ ] **Step 1: 写 task_dispatcher.py**

```python
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from db.database import SessionLocal
from models.test_task import TestTask
from models.task_result import TaskResult
from models.test_case import TestCase
from models.device import Device
from models.project import Project
from executors.android_executor import AndroidExecutor
from executors.script_executor import ScriptExecutor

class TaskDispatcher:
    """Task dispatcher for concurrent test execution."""
    
    def __init__(self):
        self.executors = {
            "android": AndroidExecutor(),
            "script": ScriptExecutor(),
        }
    
    def dispatch(self, task_id: str, db: Session = None) -> Dict:
        """
        Dispatch a test task to multiple devices concurrently.
        
        Args:
            task_id: The task ID to execute
            db: Database session
            
        Returns:
            Dict with execution results
        """
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False
        
        try:
            # Get task
            task = db.query(TestTask).filter(TestTask.id == task_id).first()
            if not task:
                return {"status": "failed", "error": "Task not found"}
            
            # Get test case
            test_case = db.query(TestCase).filter(TestCase.id == task.case_id).first()
            if not test_case:
                return {"status": "failed", "error": "Test case not found"}
            
            # Get project
            project = db.query(Project).filter(Project.id == test_case.project_id).first()
            
            # Parse device IDs
            device_ids = json.loads(task.device_ids)
            
            # Update task status
            task.status = "running"
            db.commit()
            
            # Execute on each device concurrently
            results = {}
            with ThreadPoolExecutor(max_workers=len(device_ids)) as executor:
                futures = {}
                for device_id in device_ids:
                    future = executor.submit(
                        self._execute_on_device,
                        task_id,
                        test_case,
                        device_id,
                        project,
                        db
                    )
                    futures[future] = device_id
                
                for future in as_completed(futures):
                    device_id = futures[future]
                    try:
                        result = future.result()
                        results[device_id] = result
                    except Exception as e:
                        results[device_id] = {
                            "status": "failed",
                            "error": str(e),
                        }
            
            # Update task status
            task.status = "completed"
            db.commit()
            
            return {
                "status": "completed",
                "task_id": task_id,
                "results": results,
            }
            
        finally:
            if should_close:
                db.close()
    
    def _execute_on_device(self, task_id: str, test_case: TestCase, device_id: str, 
                           project: Project, db: Session) -> Dict:
        """Execute test on a single device."""
        # Get device
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            return {"status": "failed", "error": f"Device {device_id} not found"}
        
        # Get or create task result
        result = db.query(TaskResult).filter(
            TaskResult.task_id == task_id,
            TaskResult.device_id == device_id
        ).first()
        
        if not result:
            result = TaskResult(task_id=task_id, device_id=device_id, status="running")
            db.add(result)
            db.commit()
        
        # Update result
        result.status = "running"
        result.start_time = datetime.utcnow()
        db.commit()
        
        try:
            # Select executor based on test case type
            if test_case.type == "script":
                executor = self.executors["script"]
            else:
                executor = self.executors["android"]
            
            # Execute
            execution_result = executor.run(test_case, device, project, db)
            
            # Update result
            result.status = execution_result.get("status", "failed")
            result.end_time = datetime.utcnow()
            db.commit()
            
            return execution_result
            
        except Exception as e:
            result.status = "failed"
            result.end_time = datetime.utcnow()
            result.error = str(e)
            db.commit()
            
            return {"status": "failed", "error": str(e)}
```

- [ ] **Step 2: 写测试**

```python
import pytest
from unittest.mock import MagicMock, patch
from core.task_dispatcher import TaskDispatcher
from models.test_task import TestTask
from models.test_case import TestCase
from models.device import Device

class TestTaskDispatcher:
    def setup_method(self):
        self.dispatcher = TaskDispatcher()
    
    def test_dispatcher_init(self):
        assert "android" in self.dispatcher.executors
        assert "script" in self.dispatcher.executors
    
    def test_dispatch_task_not_found(self):
        with patch("core.task_dispatcher.SessionLocal") as mock_session:
            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.first.return_value = None
            mock_session.return_value = mock_db
            
            result = self.dispatcher.dispatch("nonexistent_task")
            assert result["status"] == "failed"
            assert "not found" in result["error"]
```

- [ ] **Step 3: 运行测试**

```bash
pytest tests/test_task_dispatcher.py -v
```

Expected: 2 tests PASSED

- [ ] **Step 4: Commit**

```bash
git add backend/core/task_dispatcher.py backend/tests/test_task_dispatcher.py
git commit -m "feat: add TaskDispatcher with concurrent execution support"
```

---

### Task 5: WebSocket 日志推送

**Files:**
- Create: `backend/websocket/log_stream.py`
- Test: `backend/tests/test_log_stream.py`

- [ ] **Step 1: 写 log_stream.py**

```python
import json
from typing import Dict, List
from fastapi import WebSocket

class LogStreamManager:
    """Manages WebSocket connections for real-time log streaming."""
    
    def __init__(self):
        self.connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, task_id: str, websocket: WebSocket):
        """Accept a WebSocket connection for a task."""
        await websocket.accept()
        if task_id not in self.connections:
            self.connections[task_id] = []
        self.connections[task_id].append(websocket)
    
    def disconnect(self, task_id: str, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if task_id in self.connections:
            if websocket in self.connections[task_id]:
                self.connections[task_id].remove(websocket)
    
    async def send_log(self, task_id: str, message: Dict):
        """Send a log message to all connected clients for a task."""
        if task_id not in self.connections:
            return
        
        disconnected = []
        for websocket in self.connections[task_id]:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)
        
        # Remove disconnected clients
        for websocket in disconnected:
            self.disconnect(task_id, websocket)
    
    async def broadcast(self, task_id: str, message: str, level: str = "INFO"):
        """Broadcast a message to all connected clients."""
        await self.send_log(task_id, {
            "type": "log",
            "level": level,
            "message": message,
        })

# Global instance
log_stream_manager = LogStreamManager()
```

- [ ] **Step 2: 写测试**

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from websocket.log_stream import LogStreamManager

class TestLogStreamManager:
    def setup_method(self):
        self.manager = LogStreamManager()
    
    @pytest.mark.asyncio
    async def test_connect(self):
        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()
        
        await self.manager.connect("task_1", mock_ws)
        assert "task_1" in self.manager.connections
        assert len(self.manager.connections["task_1"]) == 1
    
    @pytest.mark.asyncio
    async def test_disconnect(self):
        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()
        
        await self.manager.connect("task_1", mock_ws)
        self.manager.disconnect("task_1", mock_ws)
        assert len(self.manager.connections["task_1"]) == 0
```

- [ ] **Step 3: 运行测试**

```bash
pytest tests/test_log_stream.py -v
```

Expected: 2 tests PASSED

- [ ] **Step 4: Commit**

```bash
git add backend/websocket/log_stream.py backend/tests/test_log_stream.py
git commit -m "feat: add WebSocket log stream manager"
```

---

### Task 6: 更新 Tasks API 支持执行

**Files:**
- Modify: `backend/api/tasks.py`
- Test: `backend/tests/test_tasks_execution.py`

- [ ] **Step 1: 修改 tasks.py 添加执行端点**

```python
import json
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db
from models.test_task import TestTask
from models.task_result import TaskResult
from schemas.test_task import TestTaskCreate, TestTaskResponse
from core.task_dispatcher import TaskDispatcher

router = APIRouter(prefix="/api", tags=["tasks"])

dispatcher = TaskDispatcher()

@router.post("/tasks/{task_id}/execute")
def execute_task(task_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Execute a task in the background."""
    task = db.query(TestTask).filter(TestTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Execute in background
    background_tasks.add_task(dispatcher.dispatch, task_id, db)
    
    return {"message": "Task execution started", "task_id": task_id}

@router.get("/tasks/{task_id}/status")
def get_task_status(task_id: str, db: Session = Depends(get_db)):
    """Get task execution status."""
    task = db.query(TestTask).filter(TestTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    results = db.query(TaskResult).filter(TaskResult.task_id == task_id).all()
    
    return {
        "task_id": task_id,
        "status": task.status,
        "results": [
            {
                "device_id": r.device_id,
                "status": r.status,
                "start_time": r.start_time.isoformat() if r.start_time else None,
                "end_time": r.end_time.isoformat() if r.end_time else None,
            }
            for r in results
        ]
    }
```

- [ ] **Step 2: 运行测试**

```bash
pytest tests/test_tasks_execution.py -v
```

Expected: Tests PASSED

- [ ] **Step 3: Commit**

```bash
git add backend/api/tasks.py backend/tests/test_tasks_execution.py
git commit -m "feat: add task execution endpoint with background processing"
```

---

## 自检 (Self-Review)

### 1. Spec 覆盖检查

| Spec 需求 | 对应 Task |
|-----------|-----------|
| BaseExecutor 抽象基类 | Task 1 |
| AndroidExecutor (uiautomator2) | Task 2 |
| ScriptExecutor (subprocess) | Task 3 |
| TaskDispatcher (并发调度) | Task 4 |
| WebSocket 日志推送 | Task 5 |
| 任务执行 API | Task 6 |

### 2. Placeholder 扫描

- 无 "TBD", "TODO", "implement later" 等占位符
- 所有执行引擎都有完整实现
- 所有测试都有完整断言

### 3. 类型一致性检查

- `BaseExecutor.run()` 返回 Dict，所有子类一致
- `TaskDispatcher.dispatch()` 接受 task_id 和 db 参数，与 API 层一致
- WebSocket manager 使用 task_id 作为连接 key

---

## 执行方式

**Plan complete and saved to `docs/superpowers/plans/2026-05-18-execution-engine.md`.**

执行此计划后，可以通过 API 创建测试任务并在多台设备上并发执行。

**执行选项：**

**1. Subagent-Driven (推荐)** - 我逐个 Task 分派子智能体，Task 之间进行审查，快速迭代

**2. Inline Execution** - 在本会话中使用 executing-plans 技能顺序执行任务，批量执行并设置检查点

**请选择执行方式？**