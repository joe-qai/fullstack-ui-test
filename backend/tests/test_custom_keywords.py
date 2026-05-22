import pytest
from fastapi.testclient import TestClient
from main import app
from core.custom_keyword_loader import validate_code

client = TestClient(app)

def test_validate_valid_code_with_function():
    """测试有效的 Python 代码包含函数定义"""
    valid, error = validate_code("def test(): pass")
    assert valid is True
    assert error == ""

def test_validate_valid_code_with_params():
    """测试有效的自定义关键字代码"""
    code = '''def custom_click(d, locator, params=None):
    """点击元素"""
    d(resourceId=locator).click()
    return True'''
    valid, error = validate_code(code)
    assert valid is True
    assert error == ""

def test_validate_invalid_code_syntax_error():
    """测试语法错误的代码"""
    valid, error = validate_code("def test(: pass")
    assert valid is False
    assert "syntax error" in error.lower()

def test_validate_empty_code():
    """测试空代码"""
    valid, error = validate_code("")
    assert valid is False
    assert "不能为空" in error

def test_validate_code_without_function():
    """测试没有函数定义的代码"""
    valid, error = validate_code("x = 1\ny = 2")
    assert valid is False
    assert "函数定义" in error

def test_validate_code_with_imports():
    """测试包含 import 语句的代码"""
    code = '''import time

def wait_and_click(d, locator, params=None):
    time.sleep(1)
    d(resourceId=locator).click()
    return True'''
    valid, error = validate_code(code)
    assert valid is True
    assert error == ""

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

def test_create_custom_keyword_without_function():
    """测试创建没有函数定义的关键字应该失败"""
    response = client.post("/api/projects/default/custom-keywords", json={
        "name": "no_function_kw",
        "description": "No function keyword",
        "code": "x = 1\ny = 2",
    })
    assert response.status_code == 400
    assert "函数定义" in response.json()["detail"]

def test_delete_custom_keyword():
    create_res = client.post("/api/projects/default/custom-keywords", json={
        "name": "delete_me_kw",
        "description": "To delete",
        "code": "def delete_me_kw(d, locator, params): pass",
    })
    kw_id = create_res.json()["id"]
    response = client.delete(f"/api/keywords/{kw_id}")
    assert response.status_code == 200
