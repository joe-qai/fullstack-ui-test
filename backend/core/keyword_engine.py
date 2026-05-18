from sqlalchemy.orm import Session
from models.keyword import Keyword


class KeywordEngine:
    BUILTIN_KEYWORDS = [
        ("click", "basic", "all", {}, "Click specified element"),
        ("input", "basic", "all", {"text": {"type": "string"}}, "Input text into element"),
        ("swipe", "basic", "all", {"direction": {"type": "string"}}, "Swipe screen"),
        ("wait_element", "basic", "all", {"timeout": {"type": "integer", "default": 10}}, "Wait for element to appear"),
        ("assert_element_exists", "basic", "all", {}, "Assert element exists"),
        ("press_back", "platform", "android", {}, "Press back button"),
        ("press_home", "platform", "android", {}, "Press home button"),
        ("scroll_to", "platform", "android", {"text": {"type": "string"}}, "Scroll to specified text"),
        ("launch_app", "platform", "android", {"package": {"type": "string"}}, "Launch specified app"),
        ("stop_app", "platform", "android", {"package": {"type": "string"}}, "Stop specified app"),
    ]

    @staticmethod
    def get_keywords(db: Session, platform: str | None = None, category: str | None = None):
        query = db.query(Keyword)
        if platform:
            query = query.filter((Keyword.platform == platform) | (Keyword.platform == "all"))
        if category:
            query = query.filter(Keyword.category == category)
        return query.all()

    @staticmethod
    def get_keyword_by_name(db: Session, name: str):
        return db.query(Keyword).filter(Keyword.name == name).first()

    @staticmethod
    def get_categories(db: Session):
        from sqlalchemy import func
        result = db.query(Keyword.category, func.count(Keyword.id)).group_by(Keyword.category).all()
        return [{"category": cat, "count": cnt} for cat, cnt in result]
