import uuid
from sqlalchemy import Column, String, Text
from models.base import Base


class Keyword(Base):
    __tablename__ = "keywords"
    id = Column(String, primary_key=True, default=lambda: f"kw_{uuid.uuid4().hex[:8]}")
    name = Column(String, nullable=False, unique=True)
    category = Column(String, nullable=False)
    platform = Column(String, default="all")
    params = Column(Text)
    description = Column(String)
    code = Column(Text)