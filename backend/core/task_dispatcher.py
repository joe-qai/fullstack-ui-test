import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, Any, List
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
            db.commit()

            return {"status": "failed", "error": str(e)}
