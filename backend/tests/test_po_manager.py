import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from db.database import SessionLocal, engine
from models.base import Base
from core.po_manager import POManager
from models.project import Project


class TestPOManager:
    def setup_method(self):
        # Ensure tables exist (creates if not already present)
        Base.metadata.create_all(bind=engine)
        self.db = SessionLocal()
        self.project = Project(name="Test Proj", app_id="com.test")
        self.db.add(self.project)
        self.db.commit()
        self.db.refresh(self.project)

    def teardown_method(self):
        self.db.close()

    def test_create_and_get_page(self):
        page = POManager.create_page(self.db, self.project.id, "LoginPage")
        assert page.name == "LoginPage"
        assert page.project_id == self.project.id

        fetched = POManager.get_page(self.db, page.id)
        assert fetched is not None
        assert fetched.name == "LoginPage"

    def test_add_and_get_element(self):
        page = POManager.create_page(self.db, self.project.id, "LoginPage")
        ele = POManager.add_element(self.db, page.id, "btn_login", "resource-id", "com.test:id/login")
        assert ele.name == "btn_login"
        assert ele.locator_type == "resource-id"

        fetched = POManager.get_element(self.db, ele.id)
        assert fetched is not None
        assert fetched.locator_value == "com.test:id/login"

    def test_delete_page_cascades_elements(self):
        page = POManager.create_page(self.db, self.project.id, "TempPage")
        ele = POManager.add_element(self.db, page.id, "btn", "xpath", "//button")

        success = POManager.delete_page(self.db, page.id)
        assert success is True
        assert POManager.get_element(self.db, ele.id) is None
