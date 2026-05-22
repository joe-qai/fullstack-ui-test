import os
import subprocess
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from db.database import get_db
from models.apk_package import APKPackage
from schemas.apk_package import APKPackageResponse
from config import settings

router = APIRouter(prefix="/api", tags=["apks"])

MAX_FILE_SIZE = 1024 * 1024 * 1024

def get_package_name(file_path: str) -> str:
    try:
        result = subprocess.run(["aapt2", "dump", "packagename", file_path], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            name = result.stdout.strip()
            if name:
                return name
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return ""

@router.get("/apks", response_model=List[APKPackageResponse])
def list_apks(db: Session = Depends(get_db)):
    return db.query(APKPackage).order_by(APKPackage.uploaded_at.desc()).all()

@router.post("/apks", response_model=APKPackageResponse)
def upload_apk(
    file: UploadFile = File(...),
    version: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    try:
        if not file.filename.endswith(".apk"):
            raise HTTPException(status_code=400, detail="Only .apk files allowed")
        
        content = file.file.read()
        file_size = len(content)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"File size exceeds {MAX_FILE_SIZE // (1024 * 1024)}MB limit")
        
        os.makedirs(settings.apks_dir, exist_ok=True)
        file_path = settings.apks_dir / file.filename
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        file_name = file.filename
        package_name = get_package_name(str(file_path))
        apk_version = version or "unknown"
        
        apk = APKPackage(
            file_name=file_name,
            package_name=package_name,
            version=apk_version,
            file_path=str(file_path),
            file_size=file_size,
            description=description
        )
        db.add(apk)
        db.commit()
        db.refresh(apk)
        return apk
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload APK: {str(e)}")

@router.delete("/apks/{apk_id}")
def delete_apk(apk_id: str, db: Session = Depends(get_db)):
    apk = db.query(APKPackage).filter(APKPackage.id == apk_id).first()
    if not apk:
        raise HTTPException(status_code=404, detail="APK not found")
    if os.path.exists(apk.file_path):
        os.remove(apk.file_path)
    db.delete(apk)
    db.commit()
    return {"message": "APK deleted"}

@router.get("/apks/{apk_id}", response_model=APKPackageResponse)
def get_apk(apk_id: str, db: Session = Depends(get_db)):
    apk = db.query(APKPackage).filter(APKPackage.id == apk_id).first()
    if not apk:
        raise HTTPException(status_code=404, detail="APK not found")
    return apk