import uuid
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from models.base import Base


class Element(Base):
    __tablename__ = "elements"
    id = Column(String, primary_key=True, default=lambda: f"ele_{uuid.uuid4().hex[:8]}")
    page_id = Column(String, ForeignKey("page_objects.id"), nullable=False)
    name = Column(String, nullable=False)
    locator_type = Column(String, nullable=False)
    locator_value = Column(String, nullable=False)
    description = Column(String)
    page_object = relationship("PageObject", back_populates="elements")
