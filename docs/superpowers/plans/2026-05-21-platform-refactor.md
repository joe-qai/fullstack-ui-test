# 前后端完全解耦+重构实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 统一端口配置、增强APK解析、优化用例/脚本管理用户体验

**Architecture:** 通过环境变量管理端口配置，实现APK多方法解析，修改数据库结构支持用例/脚本全局管理

**Tech Stack:** Python/FastAPI, Vue/Vite, SQLite, aapt/aapt2

---

## 文件结构

```
backend/
├── config.py                    # 支持环境变量
├── .env                         # 新建，后端配置
├── api/
│   ├── apks.py                 # APK多方法解析
│   ├── cases.py                # 用例API改造
│   └── scripts.py              # 脚本API改造
├── db/
│   └── database.py             # 数据库操作
└── models/
    ├── script.py               # Script模型添加project_id
    └── test_case.py            # TestCase模型添加project_id

frontend/
├── .env                        # 新建，前端配置
├── vite.config.js              # 使用环境变量
└── src/
    ├── views/
    │   ├── TestCaseManagement.vue  # 用例管理重构
    │   └── ScriptManagement.vue    # 脚本管理重构
    └── api/
        └── index.js            # API路径更新

docs/superpowers/
├── specs/2026-05-21-platform-refactor-design.md
└── plans/2026-05-21-platform-refactor.md
```

---

## Task 1: 环境配置 - 前端 .env 文件

**Files:**
- Create: `frontend/.env`
- Modify: `frontend/vite.config.js`

- [ ] **Step 1: 创建 frontend/.env 文件**

```env
VITE_API_URL=http://localhost:9000
```

- [ ] **Step 2: 修改 vite.config.js 使用环境变量**

```javascript
export default defineConfig({
  // ... existing plugins
  server: {
    port: 5174,
    proxy: {
      '/api': {
        target: import.meta.env.VITE_API_URL || 'http://localhost:9000',
        changeOrigin: true,
      },
      '/health': {
        target: import.meta.env.VITE_API_URL || 'http://localhost:9000',
        changeOrigin: true,
      },
      '/docs': {
        target: import.meta.env.VITE_API_URL || 'http://localhost:9000',
        changeOrigin: true,
      },
      '/ws': {
        target: import.meta.env.VITE_API_URL || 'http://localhost:9000',
        changeOrigin: true,
        ws: true,
      },
    },
  },
})
```

- [ ] **Step 3: 更新 frontend/.gitignore 添加 .env**

```
# environment
.env
.env.local
.env.*.local
```

- [ ] **Step 4: 提交**

```bash
git add frontend/.env frontend/vite.config.js frontend/.gitignore
git commit -m "feat: add environment variable configuration for frontend"
```

---

## Task 2: 环境配置 - 后端 .env 文件

**Files:**
- Create: `backend/.env`
- Modify: `backend/config.py`

- [ ] **Step 1: 创建 backend/.env 文件**

```env
BACKEND_PORT=9000
DATABASE_URL=sqlite:///data/autotest.db
```

- [ ] **Step 2: 修改 backend/config.py 支持环境变量**

```python
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "data" / "autotest.db"
SCRIPTS_DIR = BASE_DIR / "scripts"
REPORTS_DIR = BASE_DIR / "reports"
APKS_DIR = BASE_DIR / "data" / "apks"

os.makedirs(DB_PATH.parent, exist_ok=True)
os.makedirs(SCRIPTS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(APKS_DIR, exist_ok=True)

DATABASE_URL = f"sqlite:///{DB_PATH}"

class Settings:
    app_name: str = "UI AutoTest Platform"
    version: str = "0.1.0"
    database_url: str = os.getenv("DATABASE_URL", DATABASE_URL)
    scripts_dir: Path = SCRIPTS_DIR
    reports_dir: Path = REPORTS_DIR
    apks_dir: Path = APKS_DIR
    adb_path: str = "adb"
    device_scan_interval: int = 30
    host: str = "0.0.0.0"
    port: int = int(os.getenv("BACKEND_PORT", "9000"))
    cors_origins: list = ["http://localhost:5173", "http://localhost:5174", "http://localhost:3000", "http://localhost:9000"]

settings = Settings()
```

- [ ] **Step 3: 更新 backend/.gitignore 添加 .env**

```
# environment
.env
.env.local
.env.*.local
```

- [ ] **Step 4: 安装 python-dotenv**

```bash
cd backend
pip install python-dotenv
```

- [ ] **Step 5: 更新 backend/requirements.txt 添加 python-dotenv**

```txt
python-dotenv>=1.0.0
```

- [ ] **Step 6: 提交**

```bash
git add backend/.env backend/config.py backend/.gitignore backend/requirements.txt
git commit -m "feat: add environment variable configuration for backend"
```

---

## Task 3: 后端服务启动端口更新

**Files:**
- Modify: `backend/main.py` (if needed)
- Stop existing service on port 8000
- Start service on port 9000

- [ ] **Step 1: 停止当前后端服务**

使用 StopCommand 停止端口 8000 的进程

- [ ] **Step 2: 启动后端服务在端口 9000**

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 9000 --reload
```

- [ ] **Step 3: 验证服务启动成功**

访问 http://localhost:9000/health 确认返回 {"status":"ok"}

---

## Task 4: APK解析 - 增强多方法 fallback

**Files:**
- Modify: `backend/api/apks.py`

- [ ] **Step 1: 实现 find_aapt2_tools() 函数**

```python
def find_aapt2_tools() -> List[str]:
    """查找系统中的 aapt2 工具"""
    tools = []
    if os.name == 'nt':
        sdk_paths = [
            os.environ.get("ANDROID_HOME", ""),
            os.environ.get("ANDROID_SDK_ROOT", ""),
            os.path.expanduser(r"C:\Users\{}\AppData\Local\Android\Sdk".format(os.environ.get("USERNAME", ""))),
            r"C:\Android\Sdk",
            r"D:\Android\Sdk",
        ]
        for sdk_path in sdk_paths:
            if not sdk_path:
                continue
            build_tools = Path(sdk_path) / "build-tools"
            if build_tools.exists():
                for version_dir in sorted(build_tools.iterdir(), reverse=True):
                    aapt2_path = version_dir / "aapt2.exe"
                    if aapt2_path.exists():
                        tools.append(str(aapt2_path))
    return tools
```

- [ ] **Step 2: 实现 parse_apk_with_aapt2() 函数**

```python
def parse_apk_with_aapt2(apk_path: str, aapt2_path: str) -> Tuple[Optional[str], Optional[str]]:
    """使用 aapt2 解析 APK"""
    try:
        result = subprocess.run(
            [aapt2_path, "dump", "badging", apk_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        output = result.stdout
        package_match = re.search(r"package: name='([^']+)'", output)
        version_match = re.search(r"versionName='([^']+)'", output)
        package_name = package_match.group(1) if package_match else None
        version = version_match.group(1) if version_match else None
        return package_name, version
    except Exception as e:
        logger.warning(f"aapt2 parse failed: {e}")
        return None, None
```

- [ ] **Step 3: 实现 parse_apk_with_manifest() fallback 函数**

```python
def parse_apk_with_manifest(apk_path: str) -> Tuple[Optional[str], Optional[str]]:
    """使用 unzip 直接解析 AndroidManifest.xml"""
    try:
        with zipfile.ZipFile(apk_path, 'r') as zf:
            manifest_data = zf.read("AndroidManifest.xml")
            # 简单的二进制搜索方式提取包名
            package_match = re.search(bb'name="([^"]+)"', manifest_data)
            # 这种方法可能不够准确，需要更复杂的XML解析
            # 使用 xml.etree.ElementTree 解析
            import xml.etree.ElementTree as ET
            # AndroidManifest.xml 需要先解析二进制格式
            # 这里可以使用 axmldec 或类似工具
            return None, None
    except Exception as e:
        logger.warning(f"manifest parse failed: {e}")
        return None, None
```

- [ ] **Step 4: 修改 upload_apk() 使用多方法 fallback**

```python
@router.post("", response_model=APKPackageResponse)
def upload_apk(file: UploadFile = File(...), project_id: Optional[str] = Form(None), version: str = Form(None), description: str = Form(None), db: Session = Depends(get_db)):
    # ... 文件保存逻辑 ...

    # 多方法解析包名和版本
    package_name = None
    apk_version = version

    # 方法1: aapt2
    aapt2_tools = find_aapt2_tools()
    for aapt2_path in aapt2_tools:
        package_name, apk_version = parse_apk_with_aapt2(str(file_path), aapt2_path)
        if package_name:
            logger.info(f"Parsed APK with aapt2: {aapt2_path}")
            break

    # 方法2: aapt (原有逻辑)
    if not package_name:
        for aapt_path in find_aapt_tools():
            package_name, apk_version = parse_apk_with_aapt(str(file_path), aapt_path)
            if package_name:
                logger.info(f"Parsed APK with aapt: {aapt_path}")
                break

    # 方法3: unzip AndroidManifest.xml (保留但不依赖)
    if not package_name:
        logger.warning("All aapt tools failed, APK package info may be incomplete")

    # ... 保存逻辑 ...
```

- [ ] **Step 5: 提交**

```bash
git add backend/api/apks.py
git commit -m "feat: enhance APK parsing with aapt2 priority and fallback chain"
```

---

## Task 5: 数据库迁移 - 添加 project_id 字段

**Files:**
- Modify: `backend/models/script.py`
- Modify: `backend/models/test_case.py`
- Create: `backend/db/migrate_project_id.py`

- [ ] **Step 1: 修改 backend/models/script.py**

```python
class Script(Base):
    __tablename__ = "scripts"
    id = Column(String, primary_key=True, default=lambda: f"script_{uuid.uuid4().hex[:8]}")
    name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    type = Column(String, default="python")
    classes = Column(Text)  # JSON string
    methods = Column(Text)  # JSON string
    uploaded_at = Column(DateTime, default=utc_now)
    project_id = Column(String, nullable=False)  # 新增字段
```

- [ ] **Step 2: 修改 backend/models/test_case.py**

```python
class TestCase(Base):
    __tablename__ = "test_cases"
    id = Column(String, primary_key=True, default=lambda: f"case_{uuid.uuid4().hex[:8]}")
    name = Column(String, nullable=False)
    project_id = Column(String, nullable=False)  # 新增字段
    depends_on = Column(String)  # JSON array string
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
```

- [ ] **Step 3: 创建数据库迁移脚本 backend/db/migrate_project_id.py**

```python
#!/usr/bin/env python3
"""迁移脚本：为 scripts 和 test_cases 表添加 project_id 字段"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import engine, SessionLocal
from models.script import Script
from models.test_case import TestCase
from models.project import Project
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    from sqlalchemy import inspect, text
    
    inspector = inspect(engine)
    
    with engine.connect() as conn:
        # 检查 scripts 表是否有 project_id 列
        script_columns = [c['name'] for c in inspector.get_columns('scripts')]
        if 'project_id' not in script_columns:
            logger.info("Adding project_id to scripts table...")
            conn.execute(text("ALTER TABLE scripts ADD COLUMN project_id VARCHAR NOT NULL DEFAULT 'default'"))
            conn.commit()
            logger.info("scripts table updated")
        
        # 检查 test_cases 表是否有 project_id 列
        case_columns = [c['name'] for c in inspector.get_columns('test_cases')]
        if 'project_id' not in case_columns:
            logger.info("Adding project_id to test_cases table...")
            conn.execute(text("ALTER TABLE test_cases ADD COLUMN project_id VARCHAR NOT NULL DEFAULT 'default'"))
            conn.commit()
            logger.info("test_cases table updated")
    
    # 为现有记录设置默认 project_id
    db = SessionLocal()
    try:
        # 获取第一个项目作为默认值
        default_project = db.query(Project).first()
        if default_project:
            default_project_id = default_project.id
        else:
            # 如果没有项目，创建一个默认项目
            default_project = Project(name="Default Project", app_id="com.default")
            db.add(default_project)
            db.commit()
            db.refresh(default_project)
            default_project_id = default_project.id
            logger.info(f"Created default project: {default_project_id}")
        
        # 更新现有 scripts
        scripts_without_project = db.query(Script).filter(Script.project_id == None).all()
        for script in scripts_without_project:
            script.project_id = default_project_id
        db.commit()
        logger.info(f"Updated {len(scripts_without_project)} scripts with default project_id")
        
        # 更新现有 test_cases
        cases_without_project = db.query(TestCase).filter(TestCase.project_id == None).all()
        for case in cases_without_project:
            case.project_id = default_project_id
        db.commit()
        logger.info(f"Updated {len(cases_without_project)} test_cases with default project_id")
        
    finally:
        db.close()
    
    logger.info("Migration completed successfully")

if __name__ == "__main__":
    migrate()
```

- [ ] **Step 4: 运行迁移脚本**

```bash
cd backend
python db/migrate_project_id.py
```

- [ ] **Step 5: 提交**

```bash
git add backend/models/script.py backend/models/test_case.py backend/db/migrate_project_id.py
git commit -m "feat: add project_id to scripts and test_cases tables"
```

---

## Task 6: API适配 - 用例/脚本API改造

**Files:**
- Modify: `backend/api/cases.py`
- Modify: `backend/api/scripts.py`
- Modify: `backend/schemas/test_case.py`
- Modify: `backend/schemas/script.py`

- [ ] **Step 1: 修改 backend/schemas/test_case.py**

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TestCaseBase(BaseModel):
    name: str
    project_id: str  # 必填
    depends_on: Optional[str] = None

class TestCaseCreate(TestCaseBase):
    pass

class TestCaseUpdate(BaseModel):
    name: Optional[str] = None
    depends_on: Optional[str] = None

class TestCaseResponse(TestCaseBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

- [ ] **Step 2: 修改 backend/api/cases.py - 添加全局查询支持**

```python
@router.get("/cases", response_model=List[TestCaseResponse])
def get_all_cases(project_id: Optional[str] = None, db: Session = Depends(get_db)):
    """获取所有用例，支持按项目过滤"""
    query = db.query(TestCase)
    if project_id:
        query = query.filter(TestCase.project_id == project_id)
    return query.all()

@router.post("/cases", response_model=TestCaseResponse)
def create_case(case: TestCaseCreate, db: Session = Depends(get_db)):
    """创建用例，project_id 必填"""
    # 验证项目存在
    project = db.query(Project).filter(Project.id == case.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    db_case = TestCase(**case.model_dump())
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    return db_case
```

- [ ] **Step 3: 修改 backend/schemas/script.py**

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ScriptBase(BaseModel):
    name: str
    project_id: str  # 必填
    type: Optional[str] = "python"

class ScriptCreate(ScriptBase):
    pass

class ScriptResponse(ScriptBase):
    id: str
    file_path: str
    classes: Optional[str] = None
    methods: Optional[str] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True
```

- [ ] **Step 4: 修改 backend/api/scripts.py - 添加全局查询支持**

```python
@router.get("/scripts", response_model=List[ScriptResponse])
def get_all_scripts(project_id: Optional[str] = None, db: Session = Depends(get_db)):
    """获取所有脚本，支持按项目过滤"""
    query = db.query(Script)
    if project_id:
        query = query.filter(Script.project_id == project_id)
    return query.all()

@router.post("/{project_id}/scripts", response_model=ScriptResponse)
def upload_script(project_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """上传脚本到指定项目"""
    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    # ... 现有上传逻辑 ...
```

- [ ] **Step 5: 更新 frontend/src/api/index.js 添加全局API**

```javascript
// 全局用例API
export const getAllCases = () => api.get('/api/cases')
export const createCaseGlobal = (data) => api.post('/api/cases', data)

// 全局脚本API
export const getAllScripts = () => api.get('/api/scripts')
```

- [ ] **Step 6: 提交**

```bash
git add backend/api/cases.py backend/api/scripts.py backend/schemas/test_case.py backend/schemas/script.py frontend/src/api/index.js
git commit -m "feat: add global case/script API endpoints with project_id requirement"
```

---

## Task 7: 前端UI - 用例管理页面重构

**Files:**
- Modify: `frontend/src/views/TestCaseManagement.vue`

- [ ] **Step 1: 修改模板部分 - 添加全局新增入口**

```vue
<template>
  <div class="case-management">
    <a-page-header title="测试用例" sub-title="关键字编排 & 用例管理">
      <template #extra>
        <a-select v-model:value="selectedProject" style="width: 200px" placeholder="筛选项目(可选)" allowClear @change="fetchData">
          <a-select-option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</a-select-option>
        </a-select>
        <a-button type="primary" @click="showCreateModal">新建用例</a-button>
      </template>
    </a-page-header>
    <!-- ... 列表部分 ... -->
  </div>
</template>
```

- [ ] **Step 2: 修改脚本部分 - 添加新建弹窗逻辑**

```javascript
const showCreateModal = () => {
  createForm.value = { name: '', project_id: '', steps: [] }
  createModalVisible.value = true
}

const handleCreate = async () => {
  if (!createForm.value.project_id) {
    message.warning('请选择关联项目')
    return
  }
  // 调用 createCaseGlobal API
  await createCaseGlobal(createForm.value)
  message.success('创建成功')
  createModalVisible.value = false
  fetchData()
}
```

- [ ] **Step 3: 添加新建弹窗模板**

```vue
<a-modal v-model:open="createModalVisible" title="新建用例" @ok="handleCreate" :footer="null">
  <a-form :model="createForm" layout="vertical">
    <a-form-item label="用例名称" required>
      <a-input v-model:value="createForm.name" placeholder="请输入用例名称" />
    </a-form-item>
    <a-form-item label="关联项目" required>
      <a-select v-model:value="createForm.project_id" placeholder="请选择项目">
        <a-select-option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</a-select-option>
      </a-select>
    </a-form-item>
    <a-form-item>
      <a-button type="primary" @click="handleCreate" :disabled="!createForm.project_id">保存</a-button>
    </a-form-item>
  </a-form>
</a-modal>
```

- [ ] **Step 4: 提交**

```bash
git add frontend/src/views/TestCaseManagement.vue
git commit -m "feat: refactor test case management with global create entry"
```

---

## Task 8: 前端UI - 脚本管理页面重构

**Files:**
- Modify: `frontend/src/views/ScriptManagement.vue`

- [ ] **Step 1: 修改模板部分 - 添加全局上传入口**

```vue
<template>
  <div class="script-management">
    <a-page-header title="脚本管理" sub-title="Python脚本上传与管理">
      <template #extra>
        <a-select v-model:value="selectedProject" style="width: 200px" placeholder="筛选项目(可选)" allowClear @change="fetchData">
          <a-select-option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</a-select-option>
        </a-select>
        <a-button type="primary" @click="showUploadModal">上传脚本</a-button>
      </template>
    </a-page-header>
    <!-- ... 列表部分 ... -->
  </div>
</template>
```

- [ ] **Step 2: 添加上传弹窗逻辑**

```javascript
const uploadModalVisible = ref(false)
const uploadForm = ref({ project_id: '' })

const showUploadModal = () => {
  uploadForm.value = { project_id: selectedProject.value || '' }
  uploadModalVisible.value = true
}

const handleUpload = async (file) => {
  if (!uploadForm.value.project_id) {
    message.warning('请选择关联项目')
    return false
  }
  await uploadScript(uploadForm.value.project_id, file)
  message.success('上传成功')
  uploadModalVisible.value = false
  fetchData()
  return false // 阻止默认上传
}
```

- [ ] **Step 3: 添加上传弹窗模板**

```vue
<a-modal v-model:open="uploadModalVisible" title="上传脚本" :footer="null">
  <a-form layout="vertical">
    <a-form-item label="关联项目" required>
      <a-select v-model:value="uploadForm.project_id" placeholder="请选择项目">
        <a-select-option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</a-select-option>
      </a-select>
    </a-form-item>
    <a-form-item>
      <a-upload :custom-request="handleUpload" accept=".py" :show-upload-list="false">
        <a-button type="primary" :disabled="!uploadForm.project_id">选择文件</a-button>
      </a-upload>
    </a-form-item>
  </a-form>
</a-modal>
```

- [ ] **Step 4: 提交**

```bash
git add frontend/src/views/ScriptManagement.vue
git commit -m "feat: refactor script management with global upload entry"
```

---

## Task 9: 验证与测试

**Files:**
- All modified files

- [ ] **Step 1: 验证前端代理配置**

访问 http://localhost:5174 确认能正常加载

- [ ] **Step 2: 验证后端API**

访问 http://localhost:9000/docs 确认API文档正常

- [ ] **Step 3: 测试APK上传**

上传鹿客管家APP，确认包名为 com.lockin.loock

- [ ] **Step 4: 测试用例创建**

在无项目选中情况下点击新建用例，确认可以创建

- [ ] **Step 5: 测试脚本上传**

在无项目选中情况下点击上传脚本，确认可以上传

- [ ] **Step 6: 提交**

```bash
git add -A
git commit -m "test: verify all platform refactor changes"
```

---

## 自检清单

- [ ] 设计文档覆盖：所有需求点都有对应任务
- [ ] 占位符扫描：无 TBD/TODO/待实现 等占位符
- [ ] 类型一致性：API schema 与数据库模型一致
- [ ] 文件路径：所有路径使用绝对路径
- [ ] 命令完整性：所有命令包含预期输出

---

## 执行选项

**Plan complete and saved to `docs/superpowers/plans/2026-05-21-platform-refactor.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
