import json
from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime

class CaseStepBase(BaseModel):
    keyword_id: str
    po_element_id: str | None = None
    params: dict | None = None
    step_order: int

    @field_validator("params", mode="before")
    @classmethod
    def parse_params(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else {}
        return v or {}

class CaseStepCreate(CaseStepBase):
    pass

class CaseStepUpdate(BaseModel):
    keyword_id: str | None = None
    po_element_id: str | None = None
    params: dict | None = None
    step_order: int | None = None

class CaseStepResponse(CaseStepBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    case_id: str

class TestCaseBase(BaseModel):
    name: str
    type: str = "keyword"
    description: str | None = None
    depends_on: str | None = None
    script_id: str | None = None

class TestCaseCreate(TestCaseBase):
    steps: list[CaseStepCreate] = []

class TestCaseUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    description: str | None = None
    depends_on: str | None = None
    script_id: str | None = None
    steps: list[CaseStepCreate] | None = None

class TestCaseResponse(TestCaseBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    project_id: str
    created_at: datetime
    steps: list[CaseStepResponse] = []
