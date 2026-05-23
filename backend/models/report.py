import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from models.base import Base


def utc_now():
    return datetime.now(timezone.utc)


class Report(Base):
    __tablename__ = "reports"
    id = Column(String, primary_key=True, default=lambda: f"rpt_{uuid.uuid4().hex[:8]}")
    task_id = Column(String, ForeignKey("test_tasks.id"), nullable=False)
    name = Column(String)
    content = Column(Text, nullable=False)
    execution_time = Column(DateTime)
    created_at = Column(DateTime, default=utc_now)
