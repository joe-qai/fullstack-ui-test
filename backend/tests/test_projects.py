import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_project_with_description_and_status():
    """测试创建项目时支持描述字段，默认启用状态"""
    response = client.post("/api/projects", json={
        "name": "Test Project",
        "description": "This is a test project",
        "platform": "android"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["description"] == "This is a test project"
    assert data["status"] == "enabled"  # 默认启用
    assert "id" in data
    return data["id"]

def test_create_project_without_app_id():
    """测试创建项目不需要 app_id 字段"""
    response = client.post("/api/projects", json={
        "name": "No App ID Project",
        "platform": "android"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "No App ID Project"
    assert data["status"] == "enabled"
    assert "app_id" not in data or data.get("app_id") is None

def test_list_projects_with_status():
    """测试项目列表显示状态"""
    response = client.get("/api/projects")
    assert response.status_code == 200
    projects = response.json()
    assert isinstance(projects, list)
    for project in projects:
        assert "status" in project
        assert project["status"] in ["enabled", "disabled"]

def test_update_project_status():
    """测试更新项目状态（启用/禁用）"""
    create_res = client.post("/api/projects", json={
        "name": "Status Test Project",
        "platform": "android"
    })
    pid = create_res.json()["id"]
    
    # 禁用项目
    response = client.put(f"/api/projects/{pid}", json={"status": "disabled"})
    assert response.status_code == 200
    assert response.json()["status"] == "disabled"
    
    # 启用项目
    response = client.put(f"/api/projects/{pid}", json={"status": "enabled"})
    assert response.status_code == 200
    assert response.json()["status"] == "enabled"

def test_get_project():
    create_res = client.post("/api/projects", json={"name": "Get Test", "platform": "android"})
    pid = create_res.json()["id"]

    response = client.get(f"/api/projects/{pid}")
    assert response.status_code == 200
    assert response.json()["name"] == "Get Test"

def test_update_project():
    create_res = client.post("/api/projects", json={"name": "Update Test", "platform": "android"})
    pid = create_res.json()["id"]

    response = client.put(f"/api/projects/{pid}", json={"name": "Updated Name", "description": "Updated description"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["description"] == "Updated description"

def test_delete_project():
    create_res = client.post("/api/projects", json={"name": "Delete Test", "platform": "android"})
    pid = create_res.json()["id"]

    response = client.delete(f"/api/projects/{pid}")
    assert response.status_code == 200

    get_res = client.get(f"/api/projects/{pid}")
    assert get_res.status_code == 404

def test_get_project_stats():
    response = client.post("/api/projects", json={"name": "StatsTest", "platform": "android"})
    assert response.status_code == 200
    project_id = response.json()["id"]
    response = client.get(f"/api/projects/{project_id}/stats")
    assert response.status_code == 200
    data = response.json()
    assert "pages" in data
    assert "cases" in data
    assert "scripts" in data
    assert isinstance(data["pages"], int)
