import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from models.base import Base


def utc_now():
    return datetime.now(timezone.utc)


class Project(Base):
    __tablename__ = "projects"
    id = Column(String, primary_key=True, default=lambda: f"proj_{uuid.uuid4().hex[:8]}")
    name = Column(String, nullable=False)
    description = Column(String)
    status = Column(String, default="enabled")
    platform = Column(String, default="android")
    app_id = Column(String)
    created_at = Column(DateTime, default=utc_now)