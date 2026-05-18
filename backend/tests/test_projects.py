import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_project():
    response = client.post("/api/projects", json={"name": "Test Project", "app_id": "com.test.app", "platform": "android"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Project"
    assert "id" in data
    return data["id"]

def test_list_projects():
    response = client.get("/api/projects")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_project():
    create_res = client.post("/api/projects", json={"name": "Get Test", "app_id": "com.get"})
    pid = create_res.json()["id"]

    response = client.get(f"/api/projects/{pid}")
    assert response.status_code == 200
    assert response.json()["name"] == "Get Test"

def test_update_project():
    create_res = client.post("/api/projects", json={"name": "Update Test", "app_id": "com.update"})
    pid = create_res.json()["id"]

    response = client.put(f"/api/projects/{pid}", json={"name": "Updated Name"})
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"

def test_delete_project():
    create_res = client.post("/api/projects", json={"name": "Delete Test", "app_id": "com.delete"})
    pid = create_res.json()["id"]

    response = client.delete(f"/api/projects/{pid}")
    assert response.status_code == 200

    get_res = client.get(f"/api/projects/{pid}")
    assert get_res.status_code == 404
