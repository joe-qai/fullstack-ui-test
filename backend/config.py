import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "data" / "autotest.db"
SCRIPTS_DIR = BASE_DIR / "scripts"
REPORTS_DIR = BASE_DIR / "reports"

os.makedirs(DB_PATH.parent, exist_ok=True)
os.makedirs(SCRIPTS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

DATABASE_URL = f"sqlite:///{DB_PATH}"

class Settings:
    app_name: str = "UI AutoTest Platform"
    version: str = "0.1.0"
    database_url: str = DATABASE_URL
    scripts_dir: Path = SCRIPTS_DIR
    reports_dir: Path = REPORTS_DIR
    adb_path: str = "adb"
    device_scan_interval: int = 30
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list = ["http://localhost:5173", "http://localhost:3000"]

settings = Settings()
