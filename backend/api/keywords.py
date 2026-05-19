from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db
from models.keyword import Keyword
from schemas.keyword import KeywordCreate, KeywordResponse, KeywordCategoryResponse
from core.keyword_engine import KeywordEngine
from core.custom_keyword_loader import validate_code, write_keyword_file, reload_custom_keywords

router = APIRouter(prefix="/api", tags=["keywords"])


@router.get("/keywords", response_model=List[KeywordResponse])
def list_keywords(platform: str | None = None, category: str | None = None, db: Session = Depends(get_db)):
    return KeywordEngine.get_keywords(db, platform=platform, category=category)


@router.get("/keywords/categories", response_model=List[KeywordCategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    return KeywordEngine.get_categories(db)


@router.post("/projects/{project_id}/custom-keywords", response_model=KeywordResponse)
def create_custom_keyword(project_id: str, keyword: KeywordCreate, db: Session = Depends(get_db)):
    if keyword.code:
        valid, error = validate_code(keyword.code)
        if not valid:
            raise HTTPException(status_code=400, detail=f"Python syntax error: {error}")
        write_keyword_file(keyword.name, keyword.code)
        reload_custom_keywords()

    db_kw = Keyword(
        name=keyword.name,
        category="custom",
        platform=keyword.platform,
        params=keyword.params,
        description=keyword.description,
        code=keyword.code,
    )
    db.add(db_kw)
    db.commit()
    db.refresh(db_kw)
    return db_kw


@router.put("/keywords/{keyword_id}", response_model=KeywordResponse)
def update_custom_keyword(keyword_id: str, keyword: KeywordCreate, db: Session = Depends(get_db)):
    db_kw = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not db_kw:
        raise HTTPException(status_code=404, detail="Keyword not found")
    if db_kw.category != "custom":
        raise HTTPException(status_code=403, detail="Only custom keywords can be edited")

    if keyword.code:
        valid, error = validate_code(keyword.code)
        if not valid:
            raise HTTPException(status_code=400, detail=f"Python syntax error: {error}")
        write_keyword_file(keyword.name, keyword.code)
        reload_custom_keywords()

    db_kw.name = keyword.name
    db_kw.platform = keyword.platform
    db_kw.params = keyword.params
    db_kw.description = keyword.description
    db_kw.code = keyword.code
    db.commit()
    db.refresh(db_kw)
    return db_kw


@router.delete("/keywords/{keyword_id}")
def delete_custom_keyword(keyword_id: str, db: Session = Depends(get_db)):
    db_kw = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not db_kw:
        raise HTTPException(status_code=404, detail="Keyword not found")
    if db_kw.category != "custom":
        raise HTTPException(status_code=403, detail="Only custom keywords can be deleted")
    db.delete(db_kw)
    db.commit()
    return {"message": "Keyword deleted"}


@router.get("/projects/{project_id}/custom-keywords", response_model=List[KeywordResponse])
def list_custom_keywords(project_id: str, db: Session = Depends(get_db)):
    return db.query(Keyword).filter(Keyword.category == "custom").all()