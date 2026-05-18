from pydantic import BaseModel, ConfigDict
from datetime import datetime

class ScriptBase(BaseModel):
    name: str
    type: str = "python"
    description: str | None = None
    classes: list[str] | None = None
    methods: list[str] | None = None

class ScriptCreate(ScriptBase):
    pass

class ScriptUpdate(BaseModel):
    name: str | None = None
    description: str | None = None

class ScriptResponse(ScriptBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    project_id: str
    file_path: str
    uploaded_at: datetime
