from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db
from models.page_object import PageObject
from models.element import Element
from schemas.page_object import (
    PageObjectCreate, PageObjectUpdate, PageObjectResponse,
    ElementCreate, ElementUpdate, ElementResponse,
)

router = APIRouter(prefix="/api/projects", tags=["pages"])

@router.get("/{project_id}/pages", response_model=List[PageObjectResponse])
def list_pages(project_id: str, db: Session = Depends(get_db)):
    return db.query(PageObject).filter(PageObject.project_id == project_id).all()

@router.post("/{project_id}/pages", response_model=PageObjectResponse)
def create_page(project_id: str, page: PageObjectCreate, db: Session = Depends(get_db)):
    db_page = PageObject(project_id=project_id, name=page.name, description=page.description)
    db.add(db_page)
    db.commit()
    db.refresh(db_page)
    return db_page

@router.get("/{project_id}/pages/{page_id}", response_model=PageObjectResponse)
def get_page(project_id: str, page_id: str, db: Session = Depends(get_db)):
    page = db.query(PageObject).filter(PageObject.id == page_id, PageObject.project_id == project_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return page

@router.put("/{project_id}/pages/{page_id}", response_model=PageObjectResponse)
def update_page(project_id: str, page_id: str, page: PageObjectUpdate, db: Session = Depends(get_db)):
    db_page = db.query(PageObject).filter(PageObject.id == page_id, PageObject.project_id == project_id).first()
    if not db_page:
        raise HTTPException(status_code=404, detail="Page not found")
    update_data = page.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_page, key, value)
    db.commit()
    db.refresh(db_page)
    return db_page

@router.delete("/{project_id}/pages/{page_id}")
def delete_page(project_id: str, page_id: str, db: Session = Depends(get_db)):
    page = db.query(PageObject).filter(PageObject.id == page_id, PageObject.project_id == project_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    db.delete(page)
    db.commit()
    return {"message": "Page deleted"}

# Element endpoints
@router.get("/{project_id}/pages/{page_id}/elements", response_model=List[ElementResponse])
def list_elements(project_id: str, page_id: str, db: Session = Depends(get_db)):
    return db.query(Element).join(PageObject).filter(
        Element.page_id == page_id, PageObject.project_id == project_id
    ).all()

@router.post("/{project_id}/pages/{page_id}/elements", response_model=ElementResponse)
def create_element(project_id: str, page_id: str, element: ElementCreate, db: Session = Depends(get_db)):
    page = db.query(PageObject).filter(PageObject.id == page_id, PageObject.project_id == project_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    db_element = Element(
        page_id=page_id,
        name=element.name,
        locator_type=element.locator_type,
        locator_value=element.locator_value,
        description=element.description,
    )
    db.add(db_element)
    db.commit()
    db.refresh(db_element)
    return db_element

@router.get("/{project_id}/pages/{page_id}/elements/{element_id}", response_model=ElementResponse)
def get_element(project_id: str, page_id: str, element_id: str, db: Session = Depends(get_db)):
    element = db.query(Element).join(PageObject).filter(
        Element.id == element_id, Element.page_id == page_id, PageObject.project_id == project_id
    ).first()
    if not element:
        raise HTTPException(status_code=404, detail="Element not found")
    return element

@router.put("/{project_id}/pages/{page_id}/elements/{element_id}", response_model=ElementResponse)
def update_element(project_id: str, page_id: str, element_id: str, element: ElementUpdate, db: Session = Depends(get_db)):
    db_element = db.query(Element).join(PageObject).filter(
        Element.id == element_id, Element.page_id == page_id, PageObject.project_id == project_id
    ).first()
    if not db_element:
        raise HTTPException(status_code=404, detail="Element not found")
    update_data = element.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_element, key, value)
    db.commit()
    db.refresh(db_element)
    return db_element

@router.delete("/{project_id}/pages/{page_id}/elements/{element_id}")
def delete_element(project_id: str, page_id: str, element_id: str, db: Session = Depends(get_db)):
    element = db.query(Element).join(PageObject).filter(
        Element.id == element_id, Element.page_id == page_id, PageObject.project_id == project_id
    ).first()
    if not element:
        raise HTTPException(status_code=404, detail="Element not found")
    db.delete(element)
    db.commit()
    return {"message": "Element deleted"}
