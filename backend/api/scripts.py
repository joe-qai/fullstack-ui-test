import os
import json
import ast
import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from db.database import get_db
from models.script import Script
from schemas.script import ScriptResponse, ScriptUpdate
from config import settings

router = APIRouter(prefix="/api/projects", tags=["scripts"])

def parse_script_metadata(content: str) -> dict:
    classes = []
    methods = []
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods.append(f"{node.name}.{item.name}")
            elif isinstance(node, ast.FunctionDef) and node.name not in [m.split(".")[-1] for m in methods]:
                methods.append(node.name)
    except SyntaxError:
        pass
    return {"classes": classes, "methods": methods}

@router.get("/scripts", response_model=List[ScriptResponse])
def list_all_scripts(db: Session = Depends(get_db)):
    return db.query(Script).all()

@router.get("/{project_id}/scripts", response_model=List[ScriptResponse])
def list_scripts(project_id: str, db: Session = Depends(get_db)):
    return db.query(Script).filter(Script.project_id == project_id).all()

@router.post("/{project_id}/scripts", response_model=ScriptResponse)
def upload_script(project_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(".py"):
        raise HTTPException(status_code=400, detail="Only .py files allowed")
    
    content = file.file.read().decode("utf-8")
    metadata = parse_script_metadata(content)
    
    project_dir = settings.scripts_dir / project_id
    os.makedirs(project_dir, exist_ok=True)
    file_path = project_dir / file.filename
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    script = Script(
        project_id=project_id,
        name=file.filename,
        file_path=str(file_path),
        type="python",
        classes=json.dumps(metadata["classes"]),
        methods=json.dumps(metadata["methods"]),
    )
    db.add(script)
    db.commit()
    db.refresh(script)
    return script

@router.get("/{project_id}/scripts/{script_id}", response_model=ScriptResponse)
def get_script(project_id: str, script_id: str, db: Session = Depends(get_db)):
    script = db.query(Script).filter(Script.id == script_id, Script.project_id == project_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return script

@router.delete("/{project_id}/scripts/{script_id}")
def delete_script(project_id: str, script_id: str, db: Session = Depends(get_db)):
    script = db.query(Script).filter(Script.id == script_id, Script.project_id == project_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    if os.path.exists(script.file_path):
        os.remove(script.file_path)
    db.delete(script)
    db.commit()
    return {"message": "Script deleted"}

class BatchDeleteRequest(BaseModel):
    ids: List[str]

class ScriptContentUpdate(BaseModel):
    content: str

@router.get("/{project_id}/scripts/{script_id}/content")
def get_script_content(project_id: str, script_id: str, db: Session = Depends(get_db)):
    script = db.query(Script).filter(Script.id == script_id, Script.project_id == project_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    if not os.path.exists(script.file_path):
        raise HTTPException(status_code=404, detail="Script file not found on disk")
    with open(script.file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return {"content": content, "name": script.name}

@router.put("/{project_id}/scripts/{script_id}/content")
def update_script_content(project_id: str, script_id: str, update: ScriptContentUpdate, db: Session = Depends(get_db)):
    try:
        ast.parse(update.content)
    except SyntaxError as e:
        raise HTTPException(status_code=400, detail=f"Python syntax error: {e.msg} (line {e.lineno})")

    script = db.query(Script).filter(Script.id == script_id, Script.project_id == project_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    if not os.path.exists(script.file_path):
        raise HTTPException(status_code=404, detail="Script file not found on disk")
    with open(script.file_path, "w", encoding="utf-8") as f:
        f.write(update.content)
    metadata = parse_script_metadata(update.content)
    script.classes = json.dumps(metadata["classes"])
    script.methods = json.dumps(metadata["methods"])
    script.uploaded_at = datetime.datetime.utcnow()
    db.commit()
    return {"message": "Script content updated", "classes": metadata["classes"], "methods": metadata["methods"]}

@router.put("/{project_id}/scripts/{script_id}", response_model=ScriptResponse)
def update_script(project_id: str, script_id: str, data: ScriptUpdate, db: Session = Depends(get_db)):
    script = db.query(Script).filter(Script.id == script_id, Script.project_id == project_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(script, key, value)
    db.commit()
    db.refresh(script)
    return script

@router.post("/scripts/batch-delete")
def batch_delete_scripts(req: BatchDeleteRequest, db: Session = Depends(get_db)):
    scripts = db.query(Script).filter(Script.id.in_(req.ids)).all()
    for s in scripts:
        if os.path.exists(s.file_path):
            os.remove(s.file_path)
        db.delete(s)
    db.commit()
    return {"message": f"Deleted {len(scripts)} scripts", "count": len(scripts)}

@router.get("/{project_id}/scripts/{script_id}/download")
def download_script(project_id: str, script_id: str, db: Session = Depends(get_db)):
    script = db.query(Script).filter(Script.id == script_id, Script.project_id == project_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    if not os.path.exists(script.file_path):
        raise HTTPException(status_code=404, detail="Script file not found on disk")
    return FileResponse(script.file_path, filename=script.name, media_type="text/x-python")

@router.post("/{project_id}/scripts/{script_id}/parse")
def parse_script(project_id: str, script_id: str, db: Session = Depends(get_db)):
    script = db.query(Script).filter(Script.id == script_id, Script.project_id == project_id).first()
    if not script or not os.path.exists(script.file_path):
        raise HTTPException(status_code=404, detail="Script not found")
    with open(script.file_path, "r", encoding="utf-8") as f:
        content = f.read()
    metadata = parse_script_metadata(content)
    script.classes = json.dumps(metadata["classes"])
    script.methods = json.dumps(metadata["methods"])
    db.commit()
    db.refresh(script)
    return {"classes": metadata["classes"], "methods": metadata["methods"]}
