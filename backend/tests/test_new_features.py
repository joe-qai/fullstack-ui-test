"""Tests for new features: APK management, TestCase depends_on, Task apk_id, Device TCP/IP."""
import pytest
import io
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.database import Base, get_db
from main import app
# Import all models so metadata.create_all includes all tables
from models.project import Project
from models.page_object import PageObject
from models.element import Element
from models.keyword import Keyword
from models.test_case import TestCase
from models.case_step import CaseStep
from models.script import Script
from models.device import Device
from models.test_task import TestTask
from models.task_result import TaskResult
from models.apk_package import APKPackage

TEST_DATABASE_URL = "sqlite:///./data/test_new_features.db"
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
    # Seed keywords directly into the test DB
    db = TestingSessionLocal()
    import json
    from models.keyword import Keyword
    BUILTIN_KEYWORDS = [
        {"name": "click", "category": "basic", "platform": "all", "params": json.dumps({"type": "object", "properties": {}, "required": []}), "description": "Click specified element"},
        {"name": "input", "category": "basic", "platform": "all", "params": json.dumps({"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}), "description": "Input text into element"},
        {"name": "swipe", "category": "basic", "platform": "all", "params": json.dumps({"type": "object", "properties": {"direction": {"type": "string", "enum": ["up", "down", "left", "right"]}}, "required": ["direction"]}), "description": "Swipe screen"},
        {"name": "wait_element", "category": "basic", "platform": "all", "params": json.dumps({"type": "object", "properties": {"timeout": {"type": "integer", "default": 10}}, "required": []}), "description": "Wait for element to appear"},
        {"name": "assert_element_exists", "category": "basic", "platform": "all", "params": json.dumps({"type": "object", "properties": {}, "required": []}), "description": "Assert element exists"},
        {"name": "press_back", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {}, "required": []}), "description": "Press back button"},
        {"name": "press_home", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {}, "required": []}), "description": "Press home button"},
        {"name": "scroll_to", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}), "description": "Scroll to specified text"},
        {"name": "launch_app", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {"package": {"type": "string"}}, "required": ["package"]}), "description": "Launch specified app"},
        {"name": "stop_app", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {"package": {"type": "string"}}, "required": ["package"]}), "description": "Stop specified app"},
        {"name": "install_apk", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {"apk_id": {"type": "string"}}, "required": ["apk_id"]}), "description": "安装指定APK到设备"},
    ]
    for kw_data in BUILTIN_KEYWORDS:
        kw = Keyword(**kw_data)
        db.add(kw)
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def project_id(client):
    """Create a test project and return its ID."""
    res = client.post("/api/projects", json={
        "name": "APK Test Project",
        "app_id": "com.test.apk",
        "platform": "android",
    })
    assert res.status_code == 200
    return res.json()["id"]


# ─── APK Management Tests ───


class TestAPKManagement:
    """Test APK CRUD operations."""

    def test_list_apks_returns_empty(self, client):
        """Listing APKs with no data should return empty list."""
        res = client.get("/api/apks")
        assert res.status_code == 200
        assert res.json() == []

    def test_upload_apk_creates_entry(self, client):
        """Uploading an APK file should create a database entry."""
        fake_apk = io.BytesIO(b"fake apk content for test")
        res = client.post(
            "/api/apks",
            files={"file": ("test_app.apk", fake_apk, "application/vnd.android.package-archive")},
            data={"version": "2.1.0", "description": "Test version"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["file_name"] == "test_app.apk"
        assert data["package_name"] == "test_app"
        assert data["version"] == "2.1.0"
        assert data["description"] == "Test version"
        assert data["file_size"] > 0
        assert data["id"].startswith("apk_")

    def test_list_apks_after_upload(self, client):
        """After uploading an APK, listing APKs should include the uploaded entry."""
        fake_apk = io.BytesIO(b"list test apk")
        res = client.post(
            "/api/apks",
            files={"file": ("list_test.apk", fake_apk, "application/vnd.android.package-archive")},
            data={"version": "2.1.0"},
        )
        assert res.status_code == 200

        res = client.get("/api/apks")
        assert res.status_code == 200
        data = res.json()
        assert len(data) >= 1
        found = [a for a in data if a["version"] == "2.1.0"]
        assert len(found) >= 1

    def test_upload_apk_without_version_defaults_to_unknown(self, client):
        """Upload without version field should default to 'unknown'."""
        fake_apk = io.BytesIO(b"another fake apk")
        res = client.post(
            "/api/apks",
            files={"file": ("no_version.apk", fake_apk, "application/vnd.android.package-archive")},
        )
        assert res.status_code == 200
        assert res.json()["version"] == "unknown"

    def test_delete_apk_removes_entry(self, client):
        """Deleting an APK should remove it from the list."""
        fake_apk = io.BytesIO(b"apk to delete")
        res = client.post(
            "/api/apks",
            files={"file": ("delete_me.apk", fake_apk, "application/vnd.android.package-archive")},
            data={"version": "1.0.0"},
        )
        apk_id = res.json()["id"]

        res = client.delete(f"/api/apks/{apk_id}")
        assert res.status_code == 200

        res = client.get("/api/apks")
        remaining = [a for a in res.json() if a["id"] == apk_id]
        assert len(remaining) == 0

    def test_delete_nonexistent_apk_returns_404(self, client):
        """Deleting a non-existent APK should return 404."""
        res = client.delete("/api/apks/apk_nonexistent")
        assert res.status_code == 404

    def test_upload_non_apk_file_rejected(self, client):
        """Uploading a non-.apk file should be rejected with 400."""
        fake_txt = io.BytesIO(b"not an apk")
        res = client.post(
            "/api/apks",
            files={"file": ("test.txt", fake_txt, "text/plain")},
        )
        assert res.status_code == 400

    def test_get_apk_detail(self, client):
        """Getting APK detail by ID should return the APK info."""
        fake_apk = io.BytesIO(b"detail apk")
        res = client.post(
            "/api/apks",
            files={"file": ("detail.apk", fake_apk, "application/vnd.android.package-archive")},
            data={"version": "3.0.0"},
        )
        apk_id = res.json()["id"]

        res = client.get(f"/api/apks/{apk_id}")
        assert res.status_code == 200
        assert res.json()["id"] == apk_id
        assert res.json()["version"] == "3.0.0"


# ─── TestCase depends_on Tests ───


class TestTestCaseDependsOn:
    """Test TestCase with depends_on field."""

    def test_create_case_without_depends(self, client, project_id):
        """RED: Creating a case without depends_on should work, depends_on should be null."""
        res = client.post(f"/api/projects/{project_id}/cases", json={
            "name": "Independent Case",
            "type": "keyword",
            "description": "No dependency",
            "steps": [],
        })
        assert res.status_code == 200
        data = res.json()
        assert data["name"] == "Independent Case"
        assert data["depends_on"] is None

    def test_create_case_with_depends_on(self, client, project_id):
        """RED: Creating a case that depends on another case should persist the depends_on field."""
        res = client.post(f"/api/projects/{project_id}/cases", json={
            "name": "Prerequisite",
            "type": "keyword",
            "steps": [],
        })
        prerequisite_id = res.json()["id"]

        res = client.post(f"/api/projects/{project_id}/cases", json={
            "name": "Dependent Case",
            "type": "keyword",
            "depends_on": prerequisite_id,
            "steps": [],
        })
        assert res.status_code == 200
        data = res.json()
        assert data["depends_on"] == prerequisite_id

    def test_list_cases_shows_depends_on(self, client, project_id):
        """RED: Listing cases should include the depends_on field."""
        res = client.get(f"/api/projects/{project_id}/cases")
        assert res.status_code == 200
        for case in res.json():
            assert "depends_on" in case

    def test_update_case_depends_on(self, client, project_id):
        """RED: Updating a case should allow changing depends_on."""
        res = client.post(f"/api/projects/{project_id}/cases", json={
            "name": "Pre1", "type": "keyword", "steps": [],
        })
        pre1_id = res.json()["id"]

        res = client.post(f"/api/projects/{project_id}/cases", json={
            "name": "Pre2", "type": "keyword", "steps": [],
        })
        pre2_id = res.json()["id"]

        res = client.post(f"/api/projects/{project_id}/cases", json={
            "name": "Chain Case",
            "type": "keyword",
            "depends_on": pre1_id,
            "steps": [],
        })
        case_id = res.json()["id"]

        res = client.put(f"/api/projects/{project_id}/cases/{case_id}", json={
            "depends_on": pre2_id,
        })
        assert res.status_code == 200
        assert res.json()["depends_on"] == pre2_id

    def test_delete_case_with_dependents(self, client, project_id):
        """RED: Deleting a prerequisite case should still leave dependent case accessible."""
        res = client.post(f"/api/projects/{project_id}/cases", json={
            "name": "ToBeDeleted", "type": "keyword", "steps": [],
        })
        pre_id = res.json()["id"]

        res = client.post(f"/api/projects/{project_id}/cases", json={
            "name": "DependentOnDeleted", "type": "keyword", "depends_on": pre_id, "steps": [],
        })
        dep_id = res.json()["id"]

        res = client.delete(f"/api/projects/{project_id}/cases/{pre_id}")
        assert res.status_code == 200

        res = client.get(f"/api/projects/{project_id}/cases/{dep_id}")
        assert res.status_code == 200
        assert res.json()["depends_on"] == pre_id


# ─── Task apk_id Tests ───


class TestTaskApkId:
    """Test TestTask with apk_id field."""

    def test_create_task_without_apk_id(self, client):
        """RED: Creating a task without apk_id should work, apk_id should be null."""
        res = client.post("/api/projects", json={
            "name": "Task APK Test", "app_id": "com.taskapk", "platform": "android",
        })
        pid = res.json()["id"]
        res = client.post(f"/api/projects/{pid}/cases", json={
            "name": "Case for task", "type": "keyword", "steps": [],
        })
        case_id = res.json()["id"]

        res = client.post("/api/tasks", json={
            "case_id": case_id,
            "device_ids": [],
        })
        assert res.status_code == 200
        data = res.json()
        assert data["apk_id"] is None
        assert data["case_id"] == case_id

    def test_create_task_with_apk_id(self, client):
        """RED: Creating a task with apk_id should persist the reference."""
        res = client.post("/api/projects", json={
            "name": "Task APK Ref Test", "app_id": "com.taskapkref", "platform": "android",
        })
        pid = res.json()["id"]

        fake_apk = io.BytesIO(b"apk for task")
        res = client.post(
            "/api/apks",
            files={"file": ("task.apk", fake_apk, "application/vnd.android.package-archive")},
            data={"version": "5.0.0"},
        )
        apk_id = res.json()["id"]

        res = client.post(f"/api/projects/{pid}/cases", json={
            "name": "Case with APK", "type": "keyword", "steps": [],
        })
        case_id = res.json()["id"]

        res = client.post("/api/tasks", json={
            "case_id": case_id,
            "apk_id": apk_id,
            "device_ids": [],
        })
        assert res.status_code == 200
        data = res.json()
        assert data["apk_id"] == apk_id

    def test_task_response_includes_apk_id(self, client):
        """RED: Task response should always include apk_id field."""
        res = client.get("/api/tasks")
        assert res.status_code == 200
        for task in res.json():
            assert "apk_id" in task


# ─── Device TCP/IP Tests ───


class TestDeviceTcpip:
    """Test Device TCP/IP endpoints (mocked since no real adb in test env)."""

    def test_tcpip_endpoint_exists(self, client):
        """RED: The TCP/IP endpoint should exist and return a response."""
        res = client.post("/api/devices/tcpip", json={
            "serial": "test_device",
            "port": 5555,
        })
        assert res.status_code == 200
        data = res.json()
        assert "success" in data
        assert "message" in data

    def test_connect_endpoint_exists(self, client):
        """RED: The connect endpoint should exist and return a response."""
        res = client.post("/api/devices/connect", json={
            "ip": "192.168.1.100",
            "port": 5555,
        })
        assert res.status_code == 200
        data = res.json()
        assert "success" in data
        assert "message" in data

    def test_disconnect_endpoint_exists(self, client):
        """RED: The disconnect endpoint should exist and return a response."""
        res = client.post("/api/devices/disconnect", json={
            "ip": "192.168.1.100",
            "port": 5555,
        })
        assert res.status_code == 200
        data = res.json()
        assert "success" in data
        assert "message" in data

    def test_tcpip_default_port_is_5555(self, client):
        """RED: Calling tcpip without port should use default 5555."""
        res = client.post("/api/devices/tcpip", json={
            "serial": "test_device",
        })
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data["success"], bool)


# ─── Seed Data: install_apk Keyword ───


class TestInstallApkKeyword:
    """Test that install_apk keyword exists in seed data."""

    def test_install_apk_keyword_in_list(self, client):
        """RED: The install_apk keyword should be in the keywords list."""
        res = client.get("/api/keywords")
        assert res.status_code == 200
        keywords = res.json()
        install_apk = [kw for kw in keywords if kw["name"] == "install_apk"]
        assert len(install_apk) == 1
        assert install_apk[0]["category"] == "platform"
        assert install_apk[0]["platform"] == "android"