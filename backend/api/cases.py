from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
import json
from db.database import get_db
from models.test_case import TestCase
from models.case_step import CaseStep
from schemas.test_case import TestCaseCreate, TestCaseUpdate, TestCaseResponse, CaseStepCreate
from pydantic import BaseModel

router = APIRouter(prefix="/api/projects", tags=["cases"])

class BatchDeleteCasesRequest(BaseModel):
    ids: List[str]

@router.get("/cases", response_model=List[TestCaseResponse])
def list_all_cases(db: Session = Depends(get_db)):
    return db.query(TestCase).order_by(desc(TestCase.created_at)).all()

@router.get("/{project_id}/cases", response_model=List[TestCaseResponse])
def list_cases(project_id: str, db: Session = Depends(get_db)):
    return db.query(TestCase).filter(TestCase.project_id == project_id).order_by(desc(TestCase.created_at)).all()

@router.post("/{project_id}/cases", response_model=TestCaseResponse)
def create_case(project_id: str, case: TestCaseCreate, db: Session = Depends(get_db)):
    db_case = TestCase(
        project_id=project_id,
        name=case.name,
        type=case.type,
        description=case.description,
        depends_on=case.depends_on,
        script_id=case.script_id,
    )
    db.add(db_case)
    db.commit()
    db.refresh(db_case)

    for step in case.steps:
        db_step = CaseStep(
            case_id=db_case.id,
            keyword_id=step.keyword_id,
            po_element_id=step.po_element_id,
            params=json.dumps(step.params) if step.params else None,
            step_order=step.step_order,
        )
        db.add(db_step)
    db.commit()
    db.refresh(db_case)
    return db_case

@router.get("/{project_id}/cases/{case_id}", response_model=TestCaseResponse)
def get_case(project_id: str, case_id: str, db: Session = Depends(get_db)):
    case = db.query(TestCase).filter(TestCase.id == case_id, TestCase.project_id == project_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case

@router.put("/{project_id}/cases/{case_id}", response_model=TestCaseResponse)
def update_case(project_id: str, case_id: str, case: TestCaseUpdate, db: Session = Depends(get_db)):
    db_case = db.query(TestCase).filter(TestCase.id == case_id, TestCase.project_id == project_id).first()
    if not db_case:
        raise HTTPException(status_code=404, detail="Case not found")
    update_data = case.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key != "steps":
            setattr(db_case, key, value)
    # If steps are provided, replace all existing steps
    if "steps" in update_data and update_data["steps"] is not None:
        # Delete existing steps
        db.query(CaseStep).filter(CaseStep.case_id == case_id).delete()
        # Add new steps
        for step_data in update_data["steps"]:
            db_step = CaseStep(
                case_id=case_id,
                keyword_id=step_data.get("keyword_id"),
                po_element_id=step_data.get("po_element_id"),
                params=json.dumps(step_data.get("params")) if step_data.get("params") else None,
                step_order=step_data.get("step_order", 0),
            )
            db.add(db_step)
    db.commit()
    db.refresh(db_case)
    return db_case

@router.delete("/{project_id}/cases/{case_id}")
def delete_case(project_id: str, case_id: str, db: Session = Depends(get_db)):
    case = db.query(TestCase).filter(TestCase.id == case_id, TestCase.project_id == project_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    db.delete(case)
    db.commit()
    return {"message": "Case deleted"}

@router.post("/{project_id}/cases/{case_id}/steps")
def add_step(project_id: str, case_id: str, step: CaseStepCreate, db: Session = Depends(get_db)):
    case = db.query(TestCase).filter(TestCase.id == case_id, TestCase.project_id == project_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    db_step = CaseStep(
        case_id=case_id,
        keyword_id=step.keyword_id,
        po_element_id=step.po_element_id,
        params=json.dumps(step.params) if step.params else None,
        step_order=step.step_order,
    )
    db.add(db_step)
    db.commit()
    db.refresh(db_step)
    return db_step

@router.delete("/{project_id}/cases/{case_id}/steps/{step_id}")
def delete_step(project_id: str, case_id: str, step_id: str, db: Session = Depends(get_db)):
    step = db.query(CaseStep).join(TestCase).filter(
        CaseStep.id == step_id,
        CaseStep.case_id == case_id,
        TestCase.project_id == project_id,
    ).first()
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")
    db.delete(step)
    db.commit()
    return {"message": "Step deleted"}

@router.post("/{project_id}/cases/batch-delete")
def batch_delete_cases(project_id: str, req: BatchDeleteCasesRequest, db: Session = Depends(get_db)):
    cases = db.query(TestCase).filter(TestCase.id.in_(req.ids), TestCase.project_id == project_id).all()
    for c in cases:
        db.delete(c)
    db.commit()
    return {"message": f"Deleted {len(cases)} cases", "count": len(cases)}
