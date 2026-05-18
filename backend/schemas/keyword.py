from pydantic import BaseModel, ConfigDict

class KeywordBase(BaseModel):
    name: str
    category: str
    platform: str = "all"
    params: str | None = None
    description: str | None = None

class KeywordCreate(KeywordBase):
    pass

class KeywordResponse(KeywordBase):
    model_config = ConfigDict(from_attributes=True)
    id: str

class KeywordCategoryResponse(BaseModel):
    category: str
    count: int
