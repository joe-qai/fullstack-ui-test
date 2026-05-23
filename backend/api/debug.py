"""Debug API endpoints for uiautodev integration."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from core.uiautodev_manager import uiautodev_manager

router = APIRouter(prefix="/api/debug", tags=["debug"])

@router.get("/uiautodev/status")
def get_uiautodev_status():
    """Get uiautodev server status."""
    return uiautodev_manager.get_status()

@router.post("/uiautodev/start")
def start_uiautodev():
    """Start uiautodev server."""
    success = uiautodev_manager.start()
    return {
        "success": success,
        "status": uiautodev_manager.get_status(),
    }

@router.post("/uiautodev/stop")
def stop_uiautodev():
    """Stop uiautodev server."""
    success = uiautodev_manager.stop()
    return {
        "success": success,
        "status": uiautodev_manager.get_status(),
    }

@router.post("/uiautodev/restart")
def restart_uiautodev():
    """Restart uiautodev server."""
    success = uiautodev_manager.restart()
    return {
        "success": success,
        "status": uiautodev_manager.get_status(),
    }

@router.get("/uiautodev/device/{device_serial}")
def get_device_debug_url(device_serial: str):
    """Get uiautodev URL for a specific device."""
    return {
        "url": uiautodev_manager.get_device_url(device_serial),
        "serial": device_serial,
    }
