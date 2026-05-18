from pydantic import BaseModel, ConfigDict
from datetime import datetime

class APKPackageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    project_id: str
    version: str
    file_path: str
    file_size: int
    package_name: str | None = None
    uploaded_at: datetime
    description: str | None = None

class APKPackageCreate(BaseModel):
    version: str | None = None
    description: str | None = None