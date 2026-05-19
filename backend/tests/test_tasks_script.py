import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_task_with_case():
    proj = client.post("/api/projects", json={"name": "ScriptTaskTest", "platform": "android"})
    project_id = proj.json()["id"]
    case = client.post(f"/api/projects/{project_id}/cases", json={"name": "TestCase", "type": "keyword", "steps": []})
    case_id = case.json()["id"]
    response = client.post("/api/tasks", json={"case_id": case_id, "device_ids": ["device1"]})
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == case_id
    assert data["script_id"] is None

def test_create_task_without_case_or_script_fails():
    response = client.post("/api/tasks", json={"device_ids": ["device1"]})
    assert response.status_code == 422

def test_create_task_with_both_case_and_script_fails():
    response = client.post("/api/tasks", json={"case_id": "fake_case", "script_id": "fake_script", "device_ids": ["device1"]})
    assert response.status_code == 422