from sqlalchemy.orm import Session
from models.page_object import PageObject
from models.element import Element


class POManager:
    @staticmethod
    def create_page(db: Session, project_id: str, name: str, description: str | None = None):
        page = PageObject(project_id=project_id, name=name, description=description)
        db.add(page)
        db.commit()
        db.refresh(page)
        return page

    @staticmethod
    def get_page(db: Session, page_id: str):
        return db.query(PageObject).filter(PageObject.id == page_id).first()

    @staticmethod
    def get_pages_by_project(db: Session, project_id: str):
        return db.query(PageObject).filter(PageObject.project_id == project_id).all()

    @staticmethod
    def update_page(db: Session, page_id: str, **kwargs):
        page = db.query(PageObject).filter(PageObject.id == page_id).first()
        if not page:
            return None
        for key, value in kwargs.items():
            if value is not None and hasattr(page, key):
                setattr(page, key, value)
        db.commit()
        db.refresh(page)
        return page

    @staticmethod
    def delete_page(db: Session, page_id: str):
        page = db.query(PageObject).filter(PageObject.id == page_id).first()
        if page:
            db.delete(page)
            db.commit()
            return True
        return False

    @staticmethod
    def add_element(db: Session, page_id: str, name: str, locator_type: str, locator_value: str, description: str | None = None):
        element = Element(
            page_id=page_id,
            name=name,
            locator_type=locator_type,
            locator_value=locator_value,
            description=description,
        )
        db.add(element)
        db.commit()
        db.refresh(element)
        return element

    @staticmethod
    def get_element(db: Session, element_id: str):
        return db.query(Element).filter(Element.id == element_id).first()

    @staticmethod
    def update_element(db: Session, element_id: str, **kwargs):
        element = db.query(Element).filter(Element.id == element_id).first()
        if not element:
            return None
        for key, value in kwargs.items():
            if value is not None and hasattr(element, key):
                setattr(element, key, value)
        db.commit()
        db.refresh(element)
        return element

    @staticmethod
    def delete_element(db: Session, element_id: str):
        element = db.query(Element).filter(Element.id == element_id).first()
        if element:
            db.delete(element)
            db.commit()
            return True
        return False
