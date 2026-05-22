#!/usr/bin/env python3
"""迁移脚本：为 scripts 和 test_cases 表确保 project_id 字段存在"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import engine, SessionLocal
from models.project import Project
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate():
    from sqlalchemy import inspect, text

    inspector = inspect(engine)

    # 检查表结构
    script_columns = [c['name'] for c in inspector.get_columns('scripts')]
    logger.info(f"scripts table columns: {script_columns}")

    case_columns = [c['name'] for c in inspector.get_columns('test_cases')]
    logger.info(f"test_cases table columns: {case_columns}")

    # 获取默认项目ID
    db = SessionLocal()
    try:
        default_project = db.query(Project).first()
        if default_project:
            default_project_id = default_project.id
            logger.info(f"Default project: {default_project.name} ({default_project.id})")
        else:
            default_project = Project(name="Default Project", description="Default project", status="enabled", platform="android")
            db.add(default_project)
            db.commit()
            db.refresh(default_project)
            default_project_id = default_project.id
            logger.info(f"Created default project: {default_project_id}")
    finally:
        db.close()

    # 使用单独的连接执行更新
    with engine.connect() as conn:
        # 更新现有 scripts 中 project_id 为空的记录
        result = conn.execute(text("SELECT id FROM scripts WHERE project_id IS NULL OR project_id = ''"))
        scripts_to_update = [row[0] for row in result]
        if scripts_to_update:
            ids = ', '.join([f"'{id}'" for id in scripts_to_update])
            conn.execute(text(f"UPDATE scripts SET project_id = '{default_project_id}' WHERE id IN ({ids})"))
            conn.commit()
            logger.info(f"Updated {len(scripts_to_update)} scripts with default project_id")
        else:
            logger.info("No scripts need project_id update")

        # 更新现有 test_cases 中 project_id 为空的记录
        result = conn.execute(text("SELECT id FROM test_cases WHERE project_id IS NULL OR project_id = ''"))
        cases_to_update = [row[0] for row in result]
        if cases_to_update:
            ids = ', '.join([f"'{id}'" for id in cases_to_update])
            conn.execute(text(f"UPDATE test_cases SET project_id = '{default_project_id}' WHERE id IN ({ids})"))
            conn.commit()
            logger.info(f"Updated {len(cases_to_update)} test_cases with default project_id")
        else:
            logger.info("No test_cases need project_id update")

    logger.info("Migration completed successfully")


if __name__ == "__main__":
    migrate()