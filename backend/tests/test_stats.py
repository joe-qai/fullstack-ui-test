import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_get_stats():
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "projects" in data
    assert "cases" in data
    assert "devices" in data
    assert "tasks" in data
    assert isinstance(data["projects"], int)
    assert isinstance(data["cases"], int)
    assert isinstance(data["devices"], int)
    assert isinstance(data["tasks"], int)