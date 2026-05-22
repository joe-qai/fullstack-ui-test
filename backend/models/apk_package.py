import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime
from models.base import Base

def utc_now():
    return datetime.now(timezone.utc)

class APKPackage(Base):
    __tablename__ = "apk_packages"
    id = Column(String, primary_key=True, default=lambda: f"apk_{uuid.uuid4().hex[:8]}")
    file_name = Column(String, nullable=False)
    package_name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, default=0)
    uploaded_at = Column(DateTime, default=utc_now)
    description = Column(String)