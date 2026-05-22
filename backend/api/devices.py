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

    # 2. 等待设备重启 ADB 服务
    import time
    time.sleep(3)

    # 3. 获取设备 IP（多种方式尝试）
    ip = ""
    ip_commands = [
        [settings.adb_path, "-s", serial, "shell", "ip", "route"],
        [settings.adb_path, "-s", serial, "shell", "ifconfig", "wlan0"],
        [settings.adb_path, "-s", serial, "shell", "getprop", "dhcp.wlan0.ipaddress"],
    ]

    for cmd in ip_commands:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            output = result.stdout
            # 解析 IP，优先从 ip route 中提取 src 后的地址
            import re
            ip_match = re.search(r'src\s+(\d{1,3}(?:\.\d{1,3}){3})', output)
            if ip_match:
                ip = ip_match.group(1)
            else:
                # 备用：匹配第一个非 0.0.0.0 和非 127.x.x.x 的 IP
                ip_match = re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', output)
                if ip_match:
                    ip = ip_match.group(0)
            if ip and ip != "0.0.0.0" and not ip.startswith("127."):
                break
        except Exception:
            continue

    if not ip:
        raise HTTPException(status_code=400, detail="无法获取设备 IP 地址，请确保设备已连接 USB")

    # 4. 等待片刻后连接
    time.sleep(1)
    connect_result = DeviceScanner.connect_device(ip, 5555)
    if not connect_result["success"]:
        # 连接失败，尝试重新获取 IP 后重连
        time.sleep(2)
        connect_result = DeviceScanner.connect_device(ip, 5555)
        if not connect_result["success"]:
            raise HTTPException(status_code=400, detail=f"连接失败: {connect_result['message']}")

    # 5. 同步设备列表
    DeviceScanner.sync_devices(db)

    return {"success": True, "message": f"已连接 {ip}:5555", "serial": f"{ip}:5555"}