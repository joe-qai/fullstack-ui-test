import json
import sys
import os
from sqlalchemy import inspect, text

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
from models.apk_package import APKPackage
from models.report import Report
from core.custom_keyword_loader import ensure_directory


def migrate_project_app_id():
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    if "projects" not in tables:
        return
    columns = [col["name"] for col in inspector.get_columns("projects")]
    if "app_id" in columns:
        return
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE projects ADD COLUMN app_id VARCHAR"))

def migrate_report_name():
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    if "reports" not in tables:
        return
    columns = [col["name"] for col in inspector.get_columns("reports")]
    if "name" in columns:
        return
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE reports ADD COLUMN name VARCHAR"))
        conn.execute(text("UPDATE reports SET name = 'Report_' || substr(id, 1, 12) WHERE name IS NULL OR name = ''"))

def migrate_task_result_error():
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    if "task_results" not in tables:
        return
    columns = [col["name"] for col in inspector.get_columns("task_results")]
    if "error_message" in columns:
        return
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE task_results ADD COLUMN error_message TEXT"))

def migrate_apk_schema():
    from pathlib import Path
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    if "apk_packages" not in tables:
        return
    columns = [col["name"] for col in inspector.get_columns("apk_packages")]
    has_file_name = "file_name" in columns
    has_project_id = "project_id" in columns
    if has_file_name and not has_project_id:
        with engine.connect() as conn:
            null_count = conn.execute(text("SELECT COUNT(*) FROM apk_packages WHERE file_name IS NULL OR file_name = ''")).scalar()
        if null_count == 0:
            return
    with engine.begin() as conn:
        if not has_file_name:
            conn.execute(text("ALTER TABLE apk_packages ADD COLUMN file_name VARCHAR"))
        rows = conn.execute(text("SELECT id, file_path, package_name FROM apk_packages WHERE file_name IS NULL OR file_name = ''")).fetchall()
        for row in rows:
            fp = Path(row.file_path)
            file_name = fp.name
            pkg = row.package_name
            if not pkg and file_name.lower().endswith(".apk"):
                pkg = file_name[:-4]
            if not pkg:
                pkg = file_name
            conn.execute(
                text("UPDATE apk_packages SET file_name = :fn, package_name = :pkg WHERE id = :id"),
                {"fn": file_name, "pkg": pkg, "id": row.id},
            )
        if has_project_id:
            conn.execute(text("ALTER TABLE apk_packages DROP COLUMN project_id"))

BUILTIN_KEYWORDS = [
    {"name": "click", "category": "basic", "platform": "all", "params": json.dumps({"type": "object", "properties": {}, "required": []}), "description": "点击选中的元素"},
    {"name": "input", "category": "basic", "platform": "all", "params": json.dumps({"type": "object", "properties": {"text": {"type": "string", "description": "要输入的文本内容"}}, "required": ["text"]}), "description": "向输入框输入文本"},
    {"name": "swipe", "category": "basic", "platform": "all", "params": json.dumps({"type": "object", "properties": {"direction": {"type": "string", "enum": ["up", "down", "left", "right"], "description": "滑动方向：up上滑/down下滑/left左滑/right右滑"}}, "required": ["direction"]}), "description": "屏幕滑动操作"},
    {"name": "wait_element", "category": "basic", "platform": "all", "params": json.dumps({"type": "object", "properties": {"timeout": {"type": "integer", "default": 10, "description": "等待超时时间(秒)"}}, "required": []}), "description": "等待元素出现"},
    {"name": "press_back", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {}, "required": []}), "description": "按下返回键"},
    {"name": "press_home", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {}, "required": []}), "description": "按下Home键"},
    {"name": "scroll_to", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {"text": {"type": "string", "description": "要滚动到的文本"}}, "required": ["text"]}), "description": "滚动页面直到指定文本出现"},
    {"name": "launch_app", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {"package": {"type": "string", "description": "应用包名"}}, "required": ["package"]}), "description": "启动指定应用（通过包名）"},
    {"name": "start_app", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {"package": {"type": "string", "description": "应用包名"}}, "required": ["package"]}), "description": "启动应用（与launch_app相同）"},
    {"name": "sleep", "category": "basic", "platform": "all", "params": json.dumps({"type": "object", "properties": {"seconds": {"type": "number", "description": "等待秒数"}}, "required": ["seconds"]}), "description": "强制等待指定秒数"},
    {"name": "stop_app", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {"package": {"type": "string", "description": "应用包名"}}, "required": ["package"]}), "description": "停止指定应用"},
    {"name": "install_apk", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {"apk_id": {"type": "string", "description": "APK记录ID"}}, "required": ["apk_id"]}), "description": "安装指定APK到设备"},
    {"name": "adb_shell", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {"command": {"type": "string", "description": "要执行的adb shell命令"}}, "required": ["command"]}), "description": "执行adb shell命令"},
    {"name": "get_packages", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {"filter": {"type": "string", "description": "包名过滤关键字(可选)"}}, "required": []}), "description": "获取已安装应用包列表"},
    {"name": "get_screenshot", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {}, "required": []}), "description": "截取设备当前屏幕截图"},
    {"name": "wait_and_click", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {"timeout": {"type": "integer", "default": 10, "description": "等待超时时间(秒)"}}, "required": []}), "description": "等待元素出现后点击"},
    {"name": "ocr", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {}, "required": []}), "description": "屏幕文字识别(OCR)"},
    {"name": "find_text", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {"text": {"type": "string", "description": "要查找的文本内容"}}, "required": ["text"]}), "description": "在屏幕上查找指定文本位置"},
    {"name": "long_click", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {"duration": {"type": "integer", "default": 2000, "description": "长按持续时间(毫秒)"}}, "required": []}), "description": "长按指定元素"},
    {"name": "drag_and_drop", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {"end_x": {"type": "integer", "description": "目标位置X坐标"}, "end_y": {"type": "integer", "description": "目标位置Y坐标"}}, "required": ["end_x", "end_y"]}), "description": "拖拽元素到目标位置"},
    {"name": "wait_for_text", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {"text": {"type": "string", "description": "要等待的文本"}, "timeout": {"type": "integer", "default": 10, "description": "等待超时时间(秒)"}}, "required": ["text"]}), "description": "等待指定文本出现在屏幕上"},
    {"name": "clear_text", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {}, "required": []}), "description": "清空输入框中的文本"},
    {"name": "get_text", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {}, "required": []}), "description": "获取元素的文本内容"},
    {"name": "press_keycode", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {"keycode": {"type": "integer", "description": "Android keycode键值(如4=返回,3=Home)"}}, "required": ["keycode"]}), "description": "模拟Android物理键按下"},
    {"name": "set_orientation", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {"orientation": {"type": "string", "enum": ["portrait", "landscape"], "description": "屏幕方向：portrait竖屏/landscape横屏"}}, "required": ["orientation"]}), "description": "设置设备屏幕方向"},
    {"name": "open_notification", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {}, "required": []}), "description": "打开通知栏"},
    {"name": "get_page_source", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {}, "required": []}), "description": "获取当前页面XML布局源码"},
    {"name": "reboot_device", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {"device_id": {"type": "string", "description": "设备ID(可选，默认使用当前执行设备)"}}, "required": []}), "description": "重启设备"},
    {"name": "take_bugreport", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {"device_id": {"type": "string", "description": "设备ID(可选，默认使用当前执行设备)"}}, "required": []}), "description": "获取设备bug报告"},
    {"name": "get_battery_info", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {"device_id": {"type": "string", "description": "设备ID(可选，默认使用当前执行设备)"}}, "required": []}), "description": "获取电池状态信息"},
    {"name": "clear_app_data", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {"package": {"type": "string", "description": "应用包名"}}, "required": ["package"]}), "description": "清除应用数据"},
    {"name": "kill_app", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {"package": {"type": "string", "description": "应用包名"}}, "required": ["package"]}), "description": "强制停止应用"},
    {"name": "get_current_activity", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {"device_id": {"type": "string", "description": "设备ID(可选，默认使用当前执行设备)"}}, "required": []}), "description": "获取当前前台Activity信息"},
    {"name": "get_device_info", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {"device_id": {"type": "string", "description": "设备ID(可选，默认使用当前执行设备)"}}, "required": []}), "description": "获取设备详细信息"},
    {"name": "assert_element_exists", "category": "assertion", "platform": "all", "params": json.dumps({"type": "object", "properties": {}, "required": []}), "description": "断言元素存在"},
    {"name": "assert_element_not_exists", "category": "assertion", "platform": "all", "params": json.dumps({"type": "object", "properties": {}, "required": []}), "description": "断言元素不存在"},
    {"name": "assert_element_visible", "category": "assertion", "platform": "all", "params": json.dumps({"type": "object", "properties": {}, "required": []}), "description": "断言元素可见"},
    {"name": "assert_element_not_visible", "category": "assertion", "platform": "all", "params": json.dumps({"type": "object", "properties": {}, "required": []}), "description": "断言元素不可见"},
    {"name": "assert_element_enabled", "category": "assertion", "platform": "all", "params": json.dumps({"type": "object", "properties": {}, "required": []}), "description": "断言元素可用(未禁用)"},
    {"name": "assert_element_disabled", "category": "assertion", "platform": "all", "params": json.dumps({"type": "object", "properties": {}, "required": []}), "description": "断言元素禁用"},
    {"name": "assert_text_equals", "category": "assertion", "platform": "all", "params": json.dumps({"type": "object", "properties": {"expected": {"type": "string", "description": "期望的文本值"}}, "required": ["expected"]}), "description": "断言元素文本等于期望值"},
    {"name": "assert_text_contains", "category": "assertion", "platform": "all", "params": json.dumps({"type": "object", "properties": {"expected": {"type": "string", "description": "期望包含的文本"}}, "required": ["expected"]}), "description": "断言元素文本包含期望值"},
    {"name": "assert_text_on_screen", "category": "assertion", "platform": "android", "params": json.dumps({"type": "object", "properties": {"text": {"type": "string", "description": "要检查的文本"}}, "required": ["text"]}), "description": "断言屏幕上存在指定文本"},
    {"name": "assert_text_not_on_screen", "category": "assertion", "platform": "android", "params": json.dumps({"type": "object", "properties": {"text": {"type": "string", "description": "要检查的文本"}}, "required": ["text"]}), "description": "断言屏幕上不存在指定文本"},
]

def init_db():
    Base.metadata.create_all(bind=engine)
    migrate_project_app_id()
    migrate_apk_schema()
    migrate_report_name()
    migrate_task_result_error()
    ensure_directory()  # 确保 custom_keywords 目录存在
    db = SessionLocal()
    try:
        for kw_data in BUILTIN_KEYWORDS:
            existing = db.query(Keyword).filter(Keyword.name == kw_data["name"]).first()
            if existing:
                existing.description = kw_data["description"]
                existing.params = kw_data["params"]
                existing.category = kw_data["category"]
                existing.platform = kw_data["platform"]
            else:
                kw = Keyword(**kw_data)
                db.add(kw)
        db.commit()
        total = db.query(Keyword).count()
        print(f"Seeded keywords: {total} total")
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized")
