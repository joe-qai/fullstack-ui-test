from pydantic import BaseModel, ConfigDict
from datetime import datetime

class ProjectBase(BaseModel):
    name: str
    app_id: str | None = None
    platform: str = "android"

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: str | None = None
    app_id: str | None = None
    platform: str | None = None

class ProjectResponse(ProjectBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime
