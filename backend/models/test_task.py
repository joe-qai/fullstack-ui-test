import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from models.base import Base


def utc_now():
    return datetime.now(timezone.utc)


class TestTask(Base):
    __tablename__ = "test_tasks"
    id = Column(String, primary_key=True, default=lambda: f"task_{uuid.uuid4().hex[:8]}")
    case_id = Column(String, ForeignKey("test_cases.id"), nullable=True)
    script_id = Column(String, ForeignKey("scripts.id"), nullable=True)
    apk_id = Column(String, ForeignKey("apk_packages.id"), nullable=True)
    device_ids = Column(Text, nullable=False)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=utc_now)
    results = relationship("TaskResult", back_populates="test_task", cascade="all, delete-orphan")