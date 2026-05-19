from pydantic import BaseModel, ConfigDict, model_validator
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
    case_id: str | None = None
    script_id: str | None = None
    apk_id: str | None = None
    device_ids: list[str]
    status: str = "pending"

class TestTaskCreate(TestTaskBase):
    @model_validator(mode="after")
    def validate_case_or_script(self):
        if not self.case_id and not self.script_id:
            raise ValueError("case_id 或 script_id 必须提供一个")
        if self.case_id and self.script_id:
            raise ValueError("case_id 和 script_id 不能同时提供")
        return self

class TestTaskUpdate(BaseModel):
    status: str | None = None

class TestTaskResponse(TestTaskBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime
    results: list[TaskResultResponse] = []