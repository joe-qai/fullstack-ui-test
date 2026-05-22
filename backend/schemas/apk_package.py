from pydantic import BaseModel, ConfigDict
from datetime import datetime

class APKPackageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    file_name: str
    package_name: str
    version: str
    file_path: str
    file_size: int
    uploaded_at: datetime
    description: str | None = None

class APKPackageCreate(BaseModel):
    version: str | None = None
    description: str | None = None