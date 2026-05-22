from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime
import json

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
    
    @field_validator('classes', 'methods', mode='before')
    def parse_json_list(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, ValueError):
                return []
        return v
