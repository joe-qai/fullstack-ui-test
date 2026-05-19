import pytest
from fastapi.testclient import TestClient
from main import app
from core.custom_keyword_loader import validate_code

client = TestClient(app)

def test_validate_valid_code():
    valid, error = validate_code("def test(): pass")
    assert valid is True
    assert error == ""

def test_validate_invalid_code():
    valid, error = validate_code("def test(: pass")
    assert valid is False
    assert "Syntax error" in error

def test_create_custom_keyword():
    response = client.post("/api/projects/default/custom-keywords", json={
        "name": "custom_click_test",
        "description": "Test custom keyword",
        "platform": "android",
        "code": "def custom_click_test(d, locator, params):\n    d.click(0.5, 0.5)\n",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "custom_click_test"
    assert data["category"] == "custom"

def test_create_custom_keyword_with_syntax_error():
    response = client.post("/api/projects/default/custom-keywords", json={
        "name": "bad_keyword",
        "description": "Bad keyword",
        "code": "def bad_keyword(:\n    pass\n",
    })
    assert response.status_code == 400
    assert "syntax error" in response.json()["detail"].lower()

def test_delete_custom_keyword():
    create_res = client.post("/api/projects/default/custom-keywords", json={
        "name": "delete_me_kw",
        "description": "To delete",
        "code": "def delete_me_kw(d, locator, params): pass",
    })
    kw_id = create_res.json()["id"]
    response = client.delete(f"/api/keywords/{kw_id}")
    assert response.status_code == 200

def test_cannot_delete_builtin_keyword():
    # Use API to find a builtin keyword instead of SessionLocal
    response = client.get("/api/keywords")
    keywords = response.json()
    builtin_kw = None
    for kw in keywords:
        if kw["name"] == "click" and kw["category"] != "custom":
            builtin_kw = kw
            break
    if builtin_kw:
        response = client.delete(f"/api/keywords/{builtin_kw['id']}")
        assert response.status_code == 403