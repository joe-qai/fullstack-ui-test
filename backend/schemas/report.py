from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    task_id: str
    content: Optional[str] = None
    created_at: datetime


class ReportMetadata(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    task_id: str
    name: str | None = None
    created_at: datetime


class ReportListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    task_id: str
    name: str | None = None
    execution_time: datetime | None = None
    created_at: datetime
    task_status: str | None = None
