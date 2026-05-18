import uuid
from sqlalchemy import Column, String, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from models.base import Base


class CaseStep(Base):
    __tablename__ = "case_steps"
    id = Column(String, primary_key=True, default=lambda: f"cs_{uuid.uuid4().hex[:8]}")
    case_id = Column(String, ForeignKey("test_cases.id"), nullable=False)
    keyword_id = Column(String, ForeignKey("keywords.id"), nullable=False)
    po_element_id = Column(String, ForeignKey("elements.id"), nullable=True)
    params = Column(Text)
    step_order = Column(Integer, nullable=False)
    test_case = relationship("TestCase", back_populates="steps")
