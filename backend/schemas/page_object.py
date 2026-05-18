from pydantic import BaseModel, ConfigDict
from datetime import datetime

class ElementBase(BaseModel):
    name: str
    locator_type: str
    locator_value: str
    description: str | None = None

class ElementCreate(ElementBase):
    pass

class ElementUpdate(BaseModel):
    name: str | None = None
    locator_type: str | None = None
    locator_value: str | None = None
    description: str | None = None

class ElementResponse(ElementBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    page_id: str

class PageObjectBase(BaseModel):
    name: str
    description: str | None = None

class PageObjectCreate(PageObjectBase):
    pass

class PageObjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None

class PageObjectResponse(PageObjectBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    project_id: str
    created_at: datetime
    elements: list[ElementResponse] = []
