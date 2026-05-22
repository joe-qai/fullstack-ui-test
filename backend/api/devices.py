import json
import subprocess
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db, SessionLocal
from models.device import Device
from schemas.device import DeviceResponse
from core.device_scanner import DeviceScanner
from config import settings

router = APIRouter(prefix="/api", tags=["devices"])

def _convert_device_response(device: Device) -> Device:
    """Convert device adb_info from JSON string to dict for response."""
    if device.adb_info and isinstance(device.adb_info, str):
        try:
            device.adb_info = json.loads(device.adb_info)
        except json.JSONDecodeError:
            device.adb_info = {}
    return device

@router.get("/devices", response_model=List[DeviceResponse])
def list_devices(status: str | None = None, db: Session = Depends(get_db)):
    devices = DeviceScanner.get_devices(db, status=status)
    for device in devices:
        _convert_device_response(device)
    return devices

@router.post("/devices/scan")
def scan_devices(db: Session = Depends(get_db)):
    devices = DeviceScanner.sync_devices(db)
    for device in devices:
        _convert_device_response(device)
    return {"message": f"Scanned {len(devices)} devices", "devices": devices}

@router.get("/devices/{device_id}", response_model=DeviceResponse)
def get_device(device_id: str, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    _convert_device_response(device)
    return device

@router.get("/devices/{device_id}/status")
def get_device_status(device_id: str, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return {"serial": device.serial, "status": device.status, "platform": device.platform}

from pydantic import BaseModel

class TcpipRequest(BaseModel):
    serial: str
    port: int = 5555

class ConnectRequest(BaseModel):
    ip: str
    port: int = 5555

class DisconnectRequest(BaseModel):
    ip: str
    port: int = 5555

@router.post("/devices/tcpip")
def tcpip_device(req: TcpipRequest):
    return DeviceScanner.tcpip_device(req.serial, req.port)

@router.post("/devices/connect")
def connect_device(req: ConnectRequest):
    result = DeviceScanner.connect_device(req.ip, req.port)
    if result["success"]:
        db = SessionLocal()
        DeviceScanner.sync_devices(db)
        db.close()
    return result

@router.post("/devices/disconnect")
def disconnect_device(req: DisconnectRequest):
    result = DeviceScanner.disconnect_device(req.ip, req.port)
    db = SessionLocal()
    DeviceScanner.sync_devices(db)
    db.close()
    return result

@router.post("/devices/{serial}/connect")
def connect_device_one_click(serial: str, db: Session = Depends(get_db)):
    """一键连接 USB 设备：先 adb tcpip 开放端口，再 adb connect。"""
    
    # 检查是否已通过 TCP/IP 连接
    tcpip_devices = db.query(Device).filter(
        Device.serial.like(f"%:{serial.split(':')[0]}") |
        Device.serial.like(f"{serial.split(':')[0]}:%")
    ).all()
    
    for device in tcpip_devices:
        if device.status == "online":
            raise HTTPException(status_code=400, detail=f"设备已通过 TCP/IP 连接: {device.serial}")
    
    # 检查当前设备状态
    current_device = db.query(Device).filter(Device.serial == serial).first()
    if current_device and current_device.status != "online":
        raise HTTPException(status_code=400, detail="设备当前离线，无法进行 TCP/IP 连接")

    # 1. 切换到 tcpip 模式
    tcpip_result = DeviceScanner.tcpip_device(serial, 5555)
    if not tcpip_result["success"]:
        raise HTTPException(status_code=400, detail=tcpip_result["message"])

    # 2. 获取设备 IP
    import time
    time.sleep(1)
    devices_dict = DeviceScanner.scan_devices()
    ip = ""
    # 尝试从 adb shell 获取 IP
    try:
        result = subprocess.run(
            [settings.adb_path, "-s", serial, "shell", "ip", "route"],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.split("\n"):
            if "src" in line:
                parts = line.split()
                if "src" in parts:
                    idx = parts.index("src")
                    if idx + 1 < len(parts):
                        ip = parts[idx + 1]
                        break
    except Exception:
        pass

    if not ip:
        raise HTTPException(status_code=400, detail="无法获取设备 IP 地址")

    # 3. 连接
    connect_result = DeviceScanner.connect_device(ip, 5555)
    if not connect_result["success"]:
        raise HTTPException(status_code=400, detail=connect_result["message"])

    # 4. 同步设备列表
    DeviceScanner.sync_devices(db)

    return {"success": True, "message": f"已连接 {ip}:5555", "serial": f"{ip}:5555"}