from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db
from models.keyword import Keyword
from schemas.keyword import KeywordCreate, KeywordResponse, KeywordCategoryResponse
from core.keyword_engine import KeywordEngine

router = APIRouter(prefix="/api", tags=["keywords"])

@router.get("/keywords", response_model=List[KeywordResponse])
def list_keywords(platform: str | None = None, category: str | None = None, db: Session = Depends(get_db)):
    return KeywordEngine.get_keywords(db, platform=platform, category=category)

@router.get("/keywords/categories", response_model=List[KeywordCategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    return KeywordEngine.get_categories(db)

@router.post("/projects/{project_id}/custom-keywords", response_model=KeywordResponse)
def create_custom_keyword(project_id: str, keyword: KeywordCreate, db: Session = Depends(get_db)):
    db_kw = Keyword(
        name=keyword.name,
        category="custom",
        platform=keyword.platform,
        params=keyword.params,
        description=keyword.description,
    )
    db.add(db_kw)
    db.commit()
    db.refresh(db_kw)
    return db_kw

@router.get("/projects/{project_id}/custom-keywords", response_model=List[KeywordResponse])
def list_custom_keywords(project_id: str, db: Session = Depends(get_db)):
    return db.query(Keyword).filter(Keyword.category == "custom").all()
