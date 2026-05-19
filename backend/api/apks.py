import os
import subprocess
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db
from models.apk_package import APKPackage
from schemas.apk_package import APKPackageResponse
from config import settings

router = APIRouter(prefix="/api/projects", tags=["apks"])

def parse_apk_metadata(file_path: str) -> dict:
    try:
        result = subprocess.run(["aapt", "dump", "badging", file_path], capture_output=True, text=True, timeout=10)
        package_name = ""
        version = ""
        for line in result.stdout.split("\n"):
            if line.startswith("package: name="):
                parts = line.split()
                for part in parts:
                    if part.startswith("name="):
                        package_name = part.split("=")[1].strip("'")
                    if part.startswith("versionName="):
                        version = part.split("=")[1].strip("'")
        return {"package_name": package_name, "version": version}
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return {"package_name": "", "version": ""}

@router.get("/{project_id}/apks", response_model=List[APKPackageResponse])
def list_apks(project_id: str, db: Session = Depends(get_db)):
    return db.query(APKPackage).filter(APKPackage.project_id == project_id).all()

@router.post("/{project_id}/apks", response_model=APKPackageResponse)
def upload_apk(project_id: str, file: UploadFile = File(...), version: str = Form(None), description: str = Form(None), db: Session = Depends(get_db)):
    if not file.filename.endswith(".apk"):
        raise HTTPException(status_code=400, detail="Only .apk files allowed")
    project_dir = settings.apks_dir / project_id
    os.makedirs(project_dir, exist_ok=True)
    file_path = project_dir / file.filename
    with open(file_path, "wb") as f:
        content = file.file.read()
        f.write(content)
        file_size = len(content)
    metadata = parse_apk_metadata(str(file_path))
    apk_version = version or metadata.get("version", "unknown")
    package_name = metadata.get("package_name", "")
    apk = APKPackage(project_id=project_id, version=apk_version, file_path=str(file_path), file_size=file_size, package_name=package_name, description=description)
    db.add(apk)
    db.commit()
    db.refresh(apk)
    return apk

@router.delete("/{project_id}/apks/{apk_id}")
def delete_apk(project_id: str, apk_id: str, db: Session = Depends(get_db)):
    apk = db.query(APKPackage).filter(APKPackage.id == apk_id, APKPackage.project_id == project_id).first()
    if not apk:
        raise HTTPException(status_code=404, detail="APK not found")
    if os.path.exists(apk.file_path):
        os.remove(apk.file_path)
    db.delete(apk)
    db.commit()
    return {"message": "APK deleted"}

@router.get("/{project_id}/apks/{apk_id}", response_model=APKPackageResponse)
def get_apk(project_id: str, apk_id: str, db: Session = Depends(get_db)):
    apk = db.query(APKPackage).filter(APKPackage.id == apk_id, APKPackage.project_id == project_id).first()
    if not apk:
        raise HTTPException(status_code=404, detail="APK not found")
    return apk