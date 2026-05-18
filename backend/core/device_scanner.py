import json
import subprocess
from sqlalchemy.orm import Session
from models.device import Device
from config import settings


class DeviceScanner:
    @staticmethod
    def scan_devices():
        try:
            result = subprocess.run(
                [settings.adb_path, "devices", "-l"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            devices = {}
            for line in result.stdout.strip().split("\n")[1:]:
                parts = line.split()
                if len(parts) >= 2 and parts[1] == "device":
                    serial = parts[0]
                    info = {}
                    for part in parts[2:]:
                        if ":" in part:
                            k, v = part.split(":", 1)
                            info[k] = v
                    devices[serial] = info
            return devices
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return {}

    @staticmethod
    def sync_devices(db: Session):
        scanned = DeviceScanner.scan_devices()
        existing = {d.serial: d for d in db.query(Device).all()}

        for serial, info in scanned.items():
            if serial in existing:
                existing[serial].status = "online"
                existing[serial].adb_info = json.dumps(info)
                existing[serial].name = info.get("model", serial)
            else:
                device = Device(
                    id=serial,
                    serial=serial,
                    name=info.get("model", serial),
                    platform="android",
                    status="online",
                    adb_info=json.dumps(info),
                )
                db.add(device)

        for serial, device in existing.items():
            if serial not in scanned and device.status == "online":
                device.status = "offline"

        db.commit()
        return db.query(Device).all()

    @staticmethod
    def get_devices(db: Session, status: str | None = None):
        query = db.query(Device)
        if status:
            query = query.filter(Device.status == status)
        return query.all()
