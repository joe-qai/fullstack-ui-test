from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db
from models.device import Device
from schemas.device import DeviceResponse
from core.device_scanner import DeviceScanner

router = APIRouter(prefix="/api", tags=["devices"])

@router.get("/devices", response_model=List[DeviceResponse])
def list_devices(status: str | None = None, db: Session = Depends(get_db)):
    return DeviceScanner.get_devices(db, status=status)

@router.post("/devices/scan")
def scan_devices(db: Session = Depends(get_db)):
    devices = DeviceScanner.sync_devices(db)
    return {"message": f"Scanned {len(devices)} devices", "devices": devices}

@router.get("/devices/{device_id}", response_model=DeviceResponse)
def get_device(device_id: str, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device

@router.get("/devices/{device_id}/status")
def get_device_status(device_id: str, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return {"serial": device.serial, "status": device.status, "platform": device.platform}
