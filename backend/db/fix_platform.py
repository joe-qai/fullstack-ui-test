#!/usr/bin/env python3
"""检查并修复数据库中projects表的platform列"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import engine
from sqlalchemy import inspect, text

def fix_database():
    inspector = inspect(engine)
    
    # 检查projects表结构
    columns = inspector.get_columns('projects')
    column_names = [c['name'] for c in columns]
    print(f"projects表当前列: {column_names}")
    
    if 'platform' in column_names:
        print("发现platform列，正在删除...")
        with engine.connect() as conn:
            # SQLite不支持直接DROP COLUMN，需要创建新表并迁移数据
            conn.execute(text("""
                CREATE TABLE projects_new (
                    id VARCHAR PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    app_id VARCHAR,
                    created_at DATETIME
                )
            """))
            conn.execute(text("""
                INSERT INTO projects_new (id, name, app_id, created_at)
                SELECT id, name, app_id, created_at FROM projects
            """))
            conn.execute(text("DROP TABLE projects"))
            conn.execute(text("ALTER TABLE projects_new RENAME TO projects"))
            conn.commit()
        print("已成功删除platform列")
    else:
        print("projects表中没有platform列，无需修复")

if __name__ == "__main__":
    fix_database()