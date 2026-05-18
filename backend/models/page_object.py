import uuid
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from models.base import Base


class PageObject(Base):
    __tablename__ = "page_objects"
    id = Column(String, primary_key=True, default=lambda: f"po_{uuid.uuid4().hex[:8]}")
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    elements = relationship("Element", back_populates="page_object", cascade="all, delete-orphan")
