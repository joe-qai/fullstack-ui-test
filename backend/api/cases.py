from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import json
from db.database import get_db
from models.test_case import TestCase
from models.case_step import CaseStep
from schemas.test_case import TestCaseCreate, TestCaseUpdate, TestCaseResponse, CaseStepCreate

router = APIRouter(prefix="/api/projects", tags=["cases"])

@router.get("/{project_id}/cases", response_model=List[TestCaseResponse])
def list_cases(project_id: str, db: Session = Depends(get_db)):
    return db.query(TestCase).filter(TestCase.project_id == project_id).all()

@router.post("/{project_id}/cases", response_model=TestCaseResponse)
def create_case(project_id: str, case: TestCaseCreate, db: Session = Depends(get_db)):
    db_case = TestCase(
        project_id=project_id,
        name=case.name,
        type=case.type,
        description=case.description,
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
