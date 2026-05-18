from sqlalchemy import Column, String, Text
from models.base import Base


class Device(Base):
    __tablename__ = "devices"
    id = Column(String, primary_key=True)
    name = Column(String)
    serial = Column(String, unique=True, nullable=False)
    platform = Column(String, default="android")
    status = Column(String, default="online")
    adb_info = Column(Text)
