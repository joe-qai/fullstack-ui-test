import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db
from models.test_task import TestTask
from models.task_result import TaskResult
from schemas.test_task import TestTaskCreate, TestTaskResponse, TaskResultResponse

router = APIRouter(prefix="/api", tags=["tasks"])

@router.get("/tasks", response_model=List[TestTaskResponse])
def list_tasks(db: Session = Depends(get_db)):
    tasks = db.query(TestTask).all()
    # Convert device_ids from JSON string to list
    for task in tasks:
        if isinstance(task.device_ids, str):
            task.device_ids = json.loads(task.device_ids)
    return tasks

@router.post("/tasks", response_model=TestTaskResponse)
def create_task(task: TestTaskCreate, db: Session = Depends(get_db)):
    db_task = TestTask(
        case_id=task.case_id,
        device_ids=json.dumps(task.device_ids),
        status="pending",
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    for device_id in task.device_ids:
        result = TaskResult(task_id=db_task.id, device_id=device_id, status="pending")
        db.add(result)
    db.commit()
    db.refresh(db_task)

    # Convert device_ids to list for response
    if isinstance(db_task.device_ids, str):
        db_task.device_ids = json.loads(db_task.device_ids)
    return db_task

@router.get("/tasks/{task_id}", response_model=TestTaskResponse)
def get_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(TestTask).filter(TestTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.get("/tasks/{task_id}/reports")
def get_task_reports(task_id: str, db: Session = Depends(get_db)):
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
                "log_path": r.log_path,
                "report_path": r.report_path,
            }
            for r in results
        ]
    }
