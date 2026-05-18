import uuid
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from models.base import Base


class TestTask(Base):
    __tablename__ = "test_tasks"
    id = Column(String, primary_key=True, default=lambda: f"task_{uuid.uuid4().hex[:8]}")
    case_id = Column(String, ForeignKey("test_cases.id"), nullable=False)
    device_ids = Column(Text, nullable=False)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    results = relationship("TaskResult", back_populates="test_task", cascade="all, delete-orphan")
