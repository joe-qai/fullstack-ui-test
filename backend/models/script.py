import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, ForeignKey, Text, DateTime
from models.base import Base


def utc_now():
    return datetime.now(timezone.utc)


class Script(Base):
    __tablename__ = "scripts"
    id = Column(String, primary_key=True, default=lambda: f"sc_{uuid.uuid4().hex[:8]}")
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    type = Column(String, default="python")
    description = Column(String)
    classes = Column(Text)
    methods = Column(Text)
    uploaded_at = Column(DateTime, default=utc_now)
