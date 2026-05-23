import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from threading import Lock
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from db.database import SessionLocal
from models.test_task import TestTask
from models.task_result import TaskResult
from models.report import Report
from models.test_case import TestCase
from models.script import Script
from models.device import Device
from models.project import Project
from models.apk_package import APKPackage
from executors.android_executor import AndroidExecutor
from executors.script_executor import ScriptExecutor
from core.report_generator import ReportGenerator


class TaskDispatcher:
    def __init__(self):
        self._cancel_flags: Dict[str, bool] = {}
        self._task_processes: Dict[str, list] = {}
        self._lock = Lock()

    def cancel_task(self, task_id: str, db: Session = None) -> bool:
        with self._lock:
            self._cancel_flags[task_id] = True
            procs = self._task_processes.pop(task_id, [])
        for p in procs:
            try:
                if p.poll() is None:
                    p.terminate()
                    try:
                        p.wait(timeout=3)
                    except:
                        p.kill()
            except:
                pass
        if db:
            task = db.query(TestTask).filter(TestTask.id == task_id).first()
            if task and task.status == "running":
                task.status = "cancelled"
                results = db.query(TaskResult).filter(TaskResult.task_id == task_id).all()
                for r in results:
                    if r.status == "running":
                        r.status = "cancelled"
                        r.end_time = datetime.now(timezone.utc)
                db.commit()
        return True

    def _is_cancelled(self, task_id: str) -> bool:
        with self._lock:
            return self._cancel_flags.get(task_id, False)

    def _track_process(self, task_id: str, proc):
        if proc and proc.poll() is None:
            with self._lock:
                self._task_processes.setdefault(task_id, []).append(proc)

    def _ensure_reports_dir(self) -> str:
        from pathlib import Path
        base = Path(__file__).parent.parent.parent
        reports_dir = base / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        return str(reports_dir)

    def _generate_and_save_report(self, task_id: str, task_data: dict,
                                  device_results: List[Dict], logs: List[Dict],
                                  db: Session):
        try:
            # Convert executor statuses for report generator
            for r in device_results:
                if r.get("status") == "success":
                    r["status"] = "passed"

            generator = ReportGenerator(task_data, device_results, logs)
            html = generator.generate_html()

            # Save HTML file
            reports_dir = self._ensure_reports_dir()
            report_filename = f"report_{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            report_path = os.path.join(reports_dir, report_filename)
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(html)

            # Save to Report table
            report_record = Report(
                task_id=task_id,
                name=f"任务报告_{task_id[:12]}",
                content=html,
                execution_time=datetime.now(timezone.utc),
            )
            db.add(report_record)
            db.commit()

            # Update TaskResult report_path
            db_results = db.query(TaskResult).filter(TaskResult.task_id == task_id).all()
            for r in db_results:
                r.report_path = report_path
            db.commit()

            print(f"Report saved for task {task_id}: {report_path}")
        except Exception as e:
            print(f"Report generation failed for task {task_id}: {e}")

    def dispatch(self, task_id: str, db: Session = None) -> Dict:
        with self._lock:
            self._cancel_flags.pop(task_id, None)
            self._task_processes.pop(task_id, None)

        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False

        try:
            task = db.query(TestTask).filter(TestTask.id == task_id).first()
            if not task:
                return {"status": "failed", "error": "Task not found"}

            test_case = None
            script = None
            project = None

            apk = None
            if task.apk_id:
                apk = db.query(APKPackage).filter(APKPackage.id == task.apk_id).first()

            if task.case_id:
                test_case = db.query(TestCase).filter(TestCase.id == task.case_id).first()
                if not test_case:
                    return {"status": "failed", "error": "Test case not found"}
                project = db.query(Project).filter(Project.id == test_case.project_id).first()
            elif task.script_id:
                script = db.query(Script).filter(Script.id == task.script_id).first()
                if not script:
                    return {"status": "failed", "error": "Script not found"}
                project = db.query(Project).filter(Project.id == script.project_id).first()

            device_ids = json.loads(task.device_ids)

            if self._is_cancelled(task_id):
                task.status = "cancelled"
                db.commit()
                return {"status": "cancelled", "task_id": task_id}

            task.status = "running"
            db.commit()

            results = {}
            with ThreadPoolExecutor(max_workers=len(device_ids)) as pool:
                futures = {}
                for device_id in device_ids:
                    future = pool.submit(
                        self._execute_on_device, task_id, test_case, script, device_id, project, apk
                    )
                    futures[future] = device_id

                for future in as_completed(futures):
                    device_id = futures[future]
                    try:
                        results[device_id] = future.result()
                    except Exception as e:
                        results[device_id] = {"status": "failed", "error": str(e)}

            if self._is_cancelled(task_id):
                task.status = "cancelled"
                db.commit()
                # 中止的任务不生成报告
                return {"status": "cancelled", "task_id": task_id}

            # 根据执行结果更新任务状态
            # 如果有任何设备执行失败，任务状态为失败
            has_failure = any(r.get("status") != "success" for r in results.values())
            task.status = "failed" if has_failure else "completed"
            db.commit()

            # 只有非中止任务才生成报告
            task_data = {
                "name": f"任务_{task_id[:12]}",
                "status": task.status,
                "created_at": task.created_at.isoformat() if task.created_at else "",
            }
            all_logs = []
            device_results_list = []
            for device_id, exec_result in results.items():
                device_results_list.append({
                    "device_id": device_id,
                    "status": exec_result.get("status", "unknown"),
                    "start_time": str(exec_result.get("start_time", "")),
                    "end_time": str(exec_result.get("end_time", "")),
                })
                for log in exec_result.get("logs", []):
                    all_logs.append(log)
            self._generate_and_save_report(task_id, task_data, device_results_list, all_logs, db)

            return {"status": task.status, "task_id": task_id, "results": results}

        finally:
            with self._lock:
                self._cancel_flags.pop(task_id, None)
                self._task_processes.pop(task_id, None)
            if should_close:
                db.close()

    def _install_apk(self, apk: APKPackage, device: Device) -> Optional[str]:
        if not apk or not os.path.exists(apk.file_path):
            return "APK file not found"
        try:
            r = subprocess.run(
                ["adb", "-s", device.serial, "install", "-r", "-d", apk.file_path],
                capture_output=True, text=True, timeout=120
            )
            if r.returncode != 0:
                return f"Install failed: {r.stderr.strip() or r.stdout.strip()}"
            return None
        except subprocess.TimeoutExpired:
            return "APK install timed out"
        except Exception as e:
            return f"APK install error: {e}"

    def _execute_on_device(self, task_id: str, test_case: Optional[TestCase],
                           script: Optional[Script], device_id: str,
                           project: Optional[Project], apk: Optional[APKPackage] = None) -> Dict:
        proc_ref = [None]

        db = SessionLocal()
        try:
            device = db.query(Device).filter(Device.id == device_id).first()
            if not device:
                return {"status": "failed", "error": f"Device {device_id} not found", "logs": []}

            if self._is_cancelled(task_id):
                return {"status": "cancelled", "logs": []}

            result = db.query(TaskResult).filter(
                TaskResult.task_id == task_id, TaskResult.device_id == device_id
            ).first()
            if not result:
                result = TaskResult(task_id=task_id, device_id=device_id, status="running")
                db.add(result)
                db.commit()

            result.status = "running"
            result.start_time = datetime.now(timezone.utc)
            db.commit()

            if self._is_cancelled(task_id):
                result.status = "cancelled"
                result.end_time = datetime.now(timezone.utc)
                db.commit()
                return {"status": "cancelled", "logs": []}

            # Install APK if specified, capture error but continue
            apk_error = None
            if apk:
                apk_error = self._install_apk(apk, device)

            execution_result = {"status": "success", "logs": [], "steps": [], "error": None}

            if script:
                exe = ScriptExecutor()
                execution_result = exe.run_script(script, device, project)
                proc_ref[0] = exe.running_process
            elif test_case:
                if test_case.type == "script":
                    exe = ScriptExecutor()
                    execution_result = exe.run(test_case, device, project, db)
                    proc_ref[0] = exe.running_process
                else:
                    exe = AndroidExecutor()
                    execution_result = exe.run(test_case, device, project, db)

            # If APK install failed, note it but keep actual execution result
            if apk_error:
                execution_result.setdefault("logs", []).append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "level": "WARNING",
                    "message": f"APK安装: {apk_error}",
                })
                # Mark as failed only if the test itself didn't run
                if not script and not test_case:
                    execution_result["status"] = "failed"
                    execution_result["error"] = apk_error

            if proc_ref[0]:
                self._track_process(task_id, proc_ref[0])

            start_time_str = result.start_time.isoformat() if result.start_time else ""
            end_time_str = datetime.now(timezone.utc).isoformat()

            if self._is_cancelled(task_id):
                result.status = "cancelled"
                result.end_time = datetime.now(timezone.utc)
                db.commit()
                return {"status": "cancelled", "logs": execution_result.get("logs", []), "start_time": start_time_str, "end_time": end_time_str}

            result.status = execution_result.get("status", "failed")
            result.end_time = datetime.now(timezone.utc)
            # 保存错误信息到数据库，优先使用步骤详情
            if execution_result.get("status") != "success":
                # 查找第一个失败步骤的详细信息
                error_msg = execution_result.get("error")
                if not error_msg and execution_result.get("steps"):
                    for step in execution_result["steps"]:
                        if step.get("status") == "failed" and step.get("error"):
                            error_msg = f"Step {step.get('order')}: {step.get('keyword')} - FAILED: {step.get('error')}"
                            break
                result.error_message = error_msg
            else:
                result.error_message = None  # 成功时清空错误信息
            db.commit()

            execution_result["start_time"] = start_time_str
            execution_result["end_time"] = end_time_str

            return execution_result

        except Exception as e:
            try:
                r = db.query(TaskResult).filter(
                    TaskResult.task_id == task_id, TaskResult.device_id == device_id
                ).first()
                if r:
                    r.status = "failed"
                    r.end_time = datetime.now(timezone.utc)
                    db.commit()
            except:
                pass
            return {"status": "failed", "error": str(e), "logs": []}

        finally:
            db.close()
