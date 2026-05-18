import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from models.base import Base


def utc_now():
    return datetime.now(timezone.utc)


class TestCase(Base):
    __tablename__ = "test_cases"
    id = Column(String, primary_key=True, default=lambda: f"tc_{uuid.uuid4().hex[:8]}")
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    description = Column(String)
    depends_on = Column(String, ForeignKey("test_cases.id"), nullable=True)
    script_id = Column(String, ForeignKey("scripts.id"), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    steps = relationship("CaseStep", back_populates="test_case", cascade="all, delete-orphan", order_by="CaseStep.step_order")
