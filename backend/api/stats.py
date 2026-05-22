from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, Text
from db.database import get_db
from models.project import Project
from models.test_case import TestCase
from models.device import Device
from models.test_task import TestTask

router = APIRouter(prefix="/api", tags=["stats"])

@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    all_devices = db.query(Device).all()
    devices_usb = sum(1 for d in all_devices if ":" not in d.serial)
    devices_wifi = sum(1 for d in all_devices if ":" in d.serial)
    return {
        "projects": db.query(Project).count(),
        "cases": db.query(TestCase).count(),
        "devices": len(all_devices),
        "devices_usb": devices_usb,
        "devices_wifi": devices_wifi,
        "tasks": db.query(TestTask).count(),
    }