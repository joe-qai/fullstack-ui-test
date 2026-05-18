import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from models.base import Base


class Project(Base):
    __tablename__ = "projects"
    id = Column(String, primary_key=True, default=lambda: f"proj_{uuid.uuid4().hex[:8]}")
    name = Column(String, nullable=False)
    app_id = Column(String)
    platform = Column(String, default="android")
    created_at = Column(DateTime, default=datetime.utcnow)
