import uuid
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from models.base import Base


class TaskResult(Base):
    __tablename__ = "task_results"
    id = Column(String, primary_key=True, default=lambda: f"tr_{uuid.uuid4().hex[:8]}")
    task_id = Column(String, ForeignKey("test_tasks.id"), nullable=False)
    device_id = Column(String, ForeignKey("devices.id"), nullable=False)
    status = Column(String, default="pending")
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    log_path = Column(String)
    report_path = Column(String)
    test_task = relationship("TestTask", back_populates="results")
