import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import SessionLocal
from core.keyword_engine import KeywordEngine


class TestKeywordEngine:
    def setup_method(self):
        self.db = SessionLocal()

    def teardown_method(self):
        self.db.close()

    def test_get_keywords(self):
        keywords = KeywordEngine.get_keywords(self.db)
        assert len(keywords) >= 10
        names = [kw.name for kw in keywords]
        assert "click" in names
        assert "input" in names

    def test_get_keywords_by_platform(self):
        keywords = KeywordEngine.get_keywords(self.db, platform="android")
        names = [kw.name for kw in keywords]
        assert "press_back" in names
        assert "click" in names  # all-platform keywords also returned

    def test_get_keyword_by_name(self):
        kw = KeywordEngine.get_keyword_by_name(self.db, "click")
        assert kw is not None
        assert kw.name == "click"
        assert kw.category == "basic"

    def test_get_categories(self):
        categories = KeywordEngine.get_categories(self.db)
        assert len(categories) >= 2
        cat_names = [c["category"] for c in categories]
        assert "basic" in cat_names
        assert "platform" in cat_names
