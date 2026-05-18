from pydantic import BaseModel, ConfigDict
from datetime import datetime

class TaskResultBase(BaseModel):
    device_id: str
    status: str = "pending"
    start_time: datetime | None = None
    end_time: datetime | None = None
    log_path: str | None = None
    report_path: str | None = None

class TaskResultResponse(TaskResultBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    task_id: str

class TestTaskBase(BaseModel):
    case_id: str
    apk_id: str | None = None
    device_ids: list[str]
    status: str = "pending"

class TestTaskCreate(TestTaskBase):
    pass

class TestTaskUpdate(BaseModel):
    status: str | None = None

class TestTaskResponse(TestTaskBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime
    results: list[TaskResultResponse] = []
