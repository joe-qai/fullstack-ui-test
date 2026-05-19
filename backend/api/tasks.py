import json
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db
from models.test_task import TestTask
from models.task_result import TaskResult
from schemas.test_task import TestTaskCreate, TestTaskResponse, TaskResultResponse
from core.task_dispatcher import TaskDispatcher
from websocket.log_stream import log_stream_manager

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
        script_id=task.script_id,
        apk_id=task.apk_id,
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


task_dispatcher = TaskDispatcher()


@router.post("/tasks/{task_id}/execute")
def execute_task(task_id: str, db: Session = Depends(get_db)):
    """Execute a test task on all assigned devices."""
    task = db.query(TestTask).filter(TestTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status == "running":
        raise HTTPException(status_code=400, detail="Task is already running")
    result = task_dispatcher.dispatch(task_id, db)
    # Refresh task data after execution
    db.refresh(task)
    if isinstance(task.device_ids, str):
        task.device_ids = json.loads(task.device_ids)
    return {"task_id": task_id, "status": task.status, "results": result}

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


@router.websocket("/ws/tasks/{task_id}/logs")
async def websocket_task_logs(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for real-time task log streaming."""
    await log_stream_manager.connect(task_id, websocket)
    try:
        while True:
            # Keep connection alive by receiving messages
            data = await websocket.receive_text()
            # Handle ping/pong or other client messages if needed
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        log_stream_manager.disconnect(task_id, websocket)
    except Exception as e:
        log_stream_manager.disconnect(task_id, websocket)
