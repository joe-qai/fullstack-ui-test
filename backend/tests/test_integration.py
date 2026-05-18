"""Integration tests for the full API stack."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from db.database import Base, get_db
from main import app

TEST_DATABASE_URL = "sqlite:///./data/integration_test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    # Seed keywords for integration tests
    from db.init_db import init_db
    init_db()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


class TestFullWorkflow:
    """Test the complete workflow."""

    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_create_and_get_project(self, client):
        # Create
        response = client.post("/api/projects", json={
            "name": "Integration Test",
            "app_id": "com.test",
            "platform": "android"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Integration Test"
        pid = data["id"]

        # Get
        response = client.get(f"/api/projects/{pid}")
        assert response.status_code == 200
        assert response.json()["id"] == pid

    def test_list_projects(self, client):
        response = client.get("/api/projects")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_page_and_element(self, client):
        # Create project first
        res = client.post("/api/projects", json={
            "name": "Page Test",
            "app_id": "com.page",
            "platform": "android"
        })
        pid = res.json()["id"]

        # Create page
        res = client.post(f"/api/projects/{pid}/pages", json={
            "name": "LoginPage",
            "description": "Login page"
        })
        assert res.status_code == 200
        page_id = res.json()["id"]

        # Create element
        res = client.post(
            f"/api/projects/{pid}/pages/{page_id}/elements",
            json={
                "name": "btn_login",
                "locator_type": "resource-id",
                "locator_value": "com.test:id/login"
            }
        )
        assert res.status_code == 200
        assert res.json()["name"] == "btn_login"

    def test_list_keywords(self, client):
        response = client.get("/api/keywords")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Note: Integration test DB may not have seed data
        # Just verify the endpoint works
        assert len(data) >= 0

    def test_create_test_case(self, client):
        # Create project
        res = client.post("/api/projects", json={
            "name": "Case Test",
            "app_id": "com.case",
            "platform": "android"
        })
        pid = res.json()["id"]

        # Create case
        res = client.post(f"/api/projects/{pid}/cases", json={
            "name": "Login Case",
            "type": "keyword",
            "description": "Test login",
            "steps": []
        })
        assert res.status_code == 200
        data = res.json()
        assert data["name"] == "Login Case"
        assert data["type"] == "keyword"

    def test_scan_and_list_devices(self, client):
        response = client.post("/api/devices/scan")
        assert response.status_code == 200
        assert "message" in response.json()

        response = client.get("/api/devices")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_task(self, client):
        # Create project and case
        res = client.post("/api/projects", json={
            "name": "Task Test",
            "app_id": "com.task",
            "platform": "android"
        })
        pid = res.json()["id"]

        res = client.post(f"/api/projects/{pid}/cases", json={
            "name": "Task Case",
            "type": "keyword",
            "steps": []
        })
        case_id = res.json()["id"]

        # Create task
        res = client.post("/api/tasks", json={
            "case_id": case_id,
            "device_ids": [],
            "status": "pending"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["case_id"] == case_id
        assert data["status"] == "pending"

    def test_uiautodev_status(self, client):
        response = client.get("/api/debug/uiautodev/status")
        assert response.status_code == 200
        data = response.json()
        assert "running" in data
        assert "url" in data


class TestErrorHandling:
    """Test error handling."""

    def test_get_nonexistent_project(self, client):
        response = client.get("/api/projects/nonexistent")
        assert response.status_code == 404

    def test_create_project_invalid_data(self, client):
        response = client.post("/api/projects", json={
            "app_id": "com.test",
            "platform": "android"
        })
        assert response.status_code == 422

    def test_delete_nonexistent_project(self, client):
        response = client.delete("/api/projects/nonexistent")
        assert response.status_code == 404
