import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from db.database import Base, get_db
from main import app

# Use an in-memory DB for tests
TEST_DATABASE_URL = "sqlite:///./data/test.db"
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
    # Drop all first to ensure clean state
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    # Seed keywords using test session
    from models.keyword import Keyword
    from db.init_db import BUILTIN_KEYWORDS
    import json
    db = TestingSessionLocal()
    try:
        for kw_data in BUILTIN_KEYWORDS:
            existing = db.query(Keyword).filter(Keyword.name == kw_data["name"]).first()
            if not existing:
                kw = Keyword(**kw_data)
                db.add(kw)
        db.commit()
    finally:
        db.close()
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    return TestClient(app)
