from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.database import get_db
from models.project import Project
from models.test_case import TestCase
from models.device import Device
from models.test_task import TestTask

router = APIRouter(prefix="/api", tags=["stats"])

@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    return {
        "projects": db.query(Project).count(),
        "cases": db.query(TestCase).count(),
        "devices": db.query(Device).count(),
        "tasks": db.query(TestTask).count(),
    }