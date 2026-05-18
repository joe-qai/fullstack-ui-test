import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import engine, Base, SessionLocal
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

BUILTIN_KEYWORDS = [
    # L1 - basic operation keywords
    {"name": "click", "category": "basic", "platform": "all", "params": json.dumps({"type": "object", "properties": {}, "required": []}), "description": "Click specified element"},
    {"name": "input", "category": "basic", "platform": "all", "params": json.dumps({"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}), "description": "Input text into element"},
    {"name": "swipe", "category": "basic", "platform": "all", "params": json.dumps({"type": "object", "properties": {"direction": {"type": "string", "enum": ["up", "down", "left", "right"]}}, "required": ["direction"]}), "description": "Swipe screen"},
    {"name": "wait_element", "category": "basic", "platform": "all", "params": json.dumps({"type": "object", "properties": {"timeout": {"type": "integer", "default": 10}}, "required": []}), "description": "Wait for element to appear"},
    {"name": "assert_element_exists", "category": "basic", "platform": "all", "params": json.dumps({"type": "object", "properties": {}, "required": []}), "description": "Assert element exists"},
    # L2 - Android platform specific keywords
    {"name": "press_back", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {}, "required": []}), "description": "Press back button"},
    {"name": "press_home", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {}, "required": []}), "description": "Press home button"},
    {"name": "scroll_to", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}), "description": "Scroll to specified text"},
    {"name": "launch_app", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {"package": {"type": "string"}}, "required": ["package"]}), "description": "Launch specified app"},
    {"name": "stop_app", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {"package": {"type": "string"}}, "required": ["package"]}), "description": "Stop specified app"},
    {"name": "install_apk", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {"apk_id": {"type": "string"}}, "required": ["apk_id"]}), "description": "安装指定APK到设备"},
]

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = db.query(Keyword).first()
        if not existing:
            for kw_data in BUILTIN_KEYWORDS:
                kw = Keyword(**kw_data)
                db.add(kw)
            db.commit()
            print(f"Seeded {len(BUILTIN_KEYWORDS)} built-in keywords")
        else:
            print("Keywords already seeded, skipping")
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized")
