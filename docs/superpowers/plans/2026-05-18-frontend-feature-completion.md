# UI AutoTest Platform 前端功能补全实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 补全前端所有缺失功能——PO管理、APK管理、测试用例编排、脚本管理、Tasks修复、Devices TCP/IP增强

**Architecture:** 后端 FastAPI + SQLAlchemy 扩展模型和 API，前端 Vue 3 + Ant Design Vue 新增 4 个页面 + 修改 2 个页面 + 扩展菜单/路由/API模块。按"后端先行"策略：每个功能先做后端模型+API+测试，再做前端页面。

**Tech Stack:** Python/FastAPI/SQLAlchemy/uvicorn (后端), Vue 3/Ant Design Vue/axios/Vite (前端), adb/aapt (设备/APK操作)

---

## File Structure

### 后端新增文件
- `backend/models/apk_package.py` — APK包模型
- `backend/schemas/apk_package.py` — APK包schemas
- `backend/api/apks.py` — APK包API路由

### 后端修改文件
- `backend/models/test_task.py` — 增加 apk_id 字段
- `backend/models/test_case.py` — 增加 depends_on 字段
- `backend/db/init_db.py` — 增加 install_apk 种子数据
- `backend/api/__init__.py` — 注册 apks_router
- `backend/api/devices.py` — 增加 TCP/IP 端点
- `backend/api/cases.py` — 确认 PUT/DELETE 已有
- `backend/core/device_scanner.py` — 增加 tcpip/connect/disconnect 方法
- `backend/config.py` — 增加 apks_dir 配置
- `backend/schemas/test_task.py` — 增加 apk_id
- `backend/schemas/test_case.py` — 增加 depends_on

### 前端新增文件
- `frontend/src/views/POManagement.vue` — PO管理页面
- `frontend/src/views/APKManagement.vue` — APK管理页面
- `frontend/src/views/TestCaseManagement.vue` — 测试用例页面
- `frontend/src/views/ScriptManagement.vue` — 脚本管理页面

### 前端修改文件
- `frontend/src/App.vue` — 扩展菜单
- `frontend/src/router/index.js` — 增加4条路由
- `frontend/src/api/index.js` — 增加 APK/TCP/IP/用例 API
- `frontend/src/views/Devices.vue` — 增加 TCP/IP
- `frontend/src/views/Tasks.vue` — 修复创建弹窗

---

### Task 1: 后端 APK 模型 + Schema + 种子数据

**Files:**
- Create: `backend/models/apk_package.py`
- Create: `backend/schemas/apk_package.py`
- Modify: `backend/db/init_db.py`
- Modify: `backend/models/test_task.py`
- Modify: `backend/models/test_case.py`
- Modify: `backend/schemas/test_task.py`
- Modify: `backend/schemas/test_case.py`

- [ ] **Step 1: 创建 APKPackage 模型**

创建 `backend/models/apk_package.py`:

```python
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, ForeignKey, Integer, DateTime
from models.base import Base

def utc_now():
    return datetime.now(timezone.utc)

class APKPackage(Base):
    __tablename__ = "apk_packages"
    id = Column(String, primary_key=True, default=lambda: f"apk_{uuid.uuid4().hex[:8]}")
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    version = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, default=0)
    package_name = Column(String)
    uploaded_at = Column(DateTime, default=utc_now)
    description = Column(String)
```

- [ ] **Step 2: 创建 APKPackage schemas**

创建 `backend/schemas/apk_package.py`:

```python
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class APKPackageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    project_id: str
    version: str
    file_path: str
    file_size: int
    package_name: str | None = None
    uploaded_at: datetime
    description: str | None = None

class APKPackageCreate(BaseModel):
    version: str | None = None
    description: str | None = None
```

- [ ] **Step 3: 修改 TestTask 模型增加 apk_id**

在 `backend/models/test_task.py` 中，在 `case_id` 列之后增加:

```python
apk_id = Column(String, ForeignKey("apk_packages.id"), nullable=True)
```

- [ ] **Step 4: 修改 TestCase 模型增加 depends_on**

在 `backend/models/test_case.py` 中，在 `description` 列之后增加:

```python
depends_on = Column(String, ForeignKey("test_cases.id"), nullable=True)
```

- [ ] **Step 5: 修改 TestTask schemas 增加 apk_id**

修改 `backend/schemas/test_task.py`: 在 `TestTaskBase`, `TestTaskCreate`, `TestTaskResponse` 三个类中都增加字段 `apk_id: str | None = None`

- [ ] **Step 6: 修改 TestCase schemas 增加 depends_on**

修改 `backend/schemas/test_case.py`: 在 `TestCaseBase`, `TestCaseCreate`, `TestCaseResponse` 三个类中都增加字段 `depends_on: str | None = None`

- [ ] **Step 7: 增加 install_apk 种子数据**

在 `backend/db/init_db.py` 的 `BUILTIN_KEYWORDS` 列表末尾增加:

```python
{"name": "install_apk", "category": "platform", "platform": "android", "params": json.dumps({"type": "object", "properties": {"apk_id": {"type": "string"}}, "required": ["apk_id"]}), "description": "安装指定APK到设备"},
```

- [ ] **Step 8: 验证后端模型加载**

```bash
cd backend && python -c "from models.apk_package import APKPackage; from models.test_task import TestTask; from models.test_case import TestCase; print('OK')"
```
Expected: OK

- [ ] **Step 9: Commit**

```bash
git add backend/models/apk_package.py backend/schemas/apk_package.py backend/models/test_task.py backend/models/test_case.py backend/schemas/test_task.py backend/schemas/test_case.py backend/db/init_db.py
git commit -m "feat: add APKPackage model, apk_id on TestTask, depends_on on TestCase, install_apk seed"
```

---

### Task 2: 后端 APK API + 设备 TCP/IP API

**Files:**
- Create: `backend/api/apks.py`
- Modify: `backend/api/__init__.py`
- Modify: `backend/api/devices.py`
- Modify: `backend/core/device_scanner.py`
- Modify: `backend/config.py`

- [ ] **Step 1: 增加 APK 存储目录配置**

修改 `backend/config.py`，在 `REPORTS_DIR` 行之后增加:

```python
APKS_DIR = BASE_DIR / "data" / "apks"
os.makedirs(APKS_DIR, exist_ok=True)
```

在 `Settings` 类中增加:
```python
apks_dir: Path = APKS_DIR
```

- [ ] **Step 2: 创建 APK API 路由**

创建 `backend/api/apks.py`:

```python
import os
import subprocess
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db
from models.apk_package import APKPackage
from schemas.apk_package import APKPackageResponse
from config import settings

router = APIRouter(prefix="/api/projects", tags=["apks"])

def parse_apk_metadata(file_path: str) -> dict:
    try:
        result = subprocess.run(["aapt", "dump", "badging", file_path], capture_output=True, text=True, timeout=10)
        package_name = ""
        version = ""
        for line in result.stdout.split("\n"):
            if line.startswith("package: name="):
                parts = line.split()
                for part in parts:
                    if part.startswith("name="):
                        package_name = part.split("=")[1].strip("'")
                    if part.startswith("versionName="):
                        version = part.split("=")[1].strip("'")
        return {"package_name": package_name, "version": version}
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return {"package_name": "", "version": ""}

@router.get("/{project_id}/apks", response_model=List[APKPackageResponse])
def list_apks(project_id: str, db: Session = Depends(get_db)):
    return db.query(APKPackage).filter(APKPackage.project_id == project_id).all()

@router.post("/{project_id}/apks", response_model=APKPackageResponse)
def upload_apk(project_id: str, file: UploadFile = File(...), version: str = Form(None), description: str = Form(None), db: Session = Depends(get_db)):
    if not file.filename.endswith(".apk"):
        raise HTTPException(status_code=400, detail="Only .apk files allowed")
    project_dir = settings.apks_dir / project_id
    os.makedirs(project_dir, exist_ok=True)
    file_path = project_dir / file.filename
    with open(file_path, "wb") as f:
        content = file.file.read()
        f.write(content)
        file_size = len(content)
    metadata = parse_apk_metadata(str(file_path))
    apk_version = version or metadata.get("version", "unknown")
    package_name = metadata.get("package_name", "")
    apk = APKPackage(project_id=project_id, version=apk_version, file_path=str(file_path), file_size=file_size, package_name=package_name, description=description)
    db.add(apk)
    db.commit()
    db.refresh(apk)
    return apk

@router.delete("/{project_id}/apks/{apk_id}")
def delete_apk(project_id: str, apk_id: str, db: Session = Depends(get_db)):
    apk = db.query(APKPackage).filter(APKPackage.id == apk_id, APKPackage.project_id == project_id).first()
    if not apk:
        raise HTTPException(status_code=404, detail="APK not found")
    if os.path.exists(apk.file_path):
        os.remove(apk.file_path)
    db.delete(apk)
    db.commit()
    return {"message": "APK deleted"}
```

- [ ] **Step 3: 注册 APK 路由**

修改 `backend/api/__init__.py`，增加 import 和 include:

```python
from api.apks import router as apks_router
```

```python
api_router.include_router(apks_router)
```

- [ ] **Step 4: 增加 Device TCP/IP 方法**

修改 `backend/core/device_scanner.py`，在类末尾增加:

```python
@staticmethod
def tcpip_device(serial: str, port: int = 5555) -> dict:
    try:
        result = subprocess.run([settings.adb_path, "-s", serial, "tcpip", str(port)], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return {"success": True, "message": f"Device {serial} switched to TCP/IP mode on port {port}"}
        return {"success": False, "message": result.stderr.strip()}
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return {"success": False, "message": str(e)}

@staticmethod
def connect_device(ip: str, port: int = 5555) -> dict:
    try:
        result = subprocess.run([settings.adb_path, "connect", f"{ip}:{port}"], capture_output=True, text=True, timeout=10)
        if "connected" in result.stdout.lower():
            return {"success": True, "message": f"Connected to {ip}:{port}", "serial": f"{ip}:{port}"}
        return {"success": False, "message": result.stdout.strip()}
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return {"success": False, "message": str(e)}

@staticmethod
def disconnect_device(ip: str, port: int = 5555) -> dict:
    try:
        result = subprocess.run([settings.adb_path, "disconnect", f"{ip}:{port}"], capture_output=True, text=True, timeout=10)
        return {"success": True, "message": f"Disconnected from {ip}:{port}"}
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return {"success": False, "message": str(e)}
```

- [ ] **Step 5: 增加 Device TCP/IP API 端点**

修改 `backend/api/devices.py`，在头部增加 `from db.database import SessionLocal` import，并在文件末尾增加:

```python
from pydantic import BaseModel

class TcpipRequest(BaseModel):
    serial: str
    port: int = 5555

class ConnectRequest(BaseModel):
    ip: str
    port: int = 5555

class DisconnectRequest(BaseModel):
    ip: str
    port: int = 5555

@router.post("/devices/tcpip")
def tcpip_device(req: TcpipRequest):
    return DeviceScanner.tcpip_device(req.serial, req.port)

@router.post("/devices/connect")
def connect_device(req: ConnectRequest):
    result = DeviceScanner.connect_device(req.ip, req.port)
    if result["success"]:
        db = SessionLocal()
        DeviceScanner.sync_devices(db)
        db.close()
    return result

@router.post("/devices/disconnect")
def disconnect_device(req: DisconnectRequest):
    result = DeviceScanner.disconnect_device(req.ip, req.port)
    db = SessionLocal()
    DeviceScanner.sync_devices(db)
    db.close()
    return result
```

- [ ] **Step 6: 验证路由注册**

```bash
cd backend && python -c "from main import app; routes = [r.path for r in app.routes if hasattr(r, 'path')]; apk_routes = [r for r in routes if 'apk' in r]; tcp_routes = [r for r in routes if 'tcpip' in r or 'connect' in r or 'disconnect' in r]; print('APK routes:', apk_routes); print('TCP routes:', tcp_routes)"
```
Expected: APK 路由和 TCP/IP 路由都出现

- [ ] **Step 7: 重建数据库**

```bash
rm -f backend/data/autotest.db
cd backend && python -c "from db.init_db import init_db; init_db(); print('Database rebuilt')"
```
Expected: "Database rebuilt" 和 "Seeded 11 built-in keywords" (原来10个 + install_apk)

- [ ] **Step 8: Commit**

```bash
git add backend/api/apks.py backend/api/__init__.py backend/api/devices.py backend/core/device_scanner.py backend/config.py
git commit -m "feat: add APK API routes, device TCP/IP API, device scanner TCP/IP methods"
```

---

### Task 3: 前端路由 + 菜单 + API模块扩展

**Files:**
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/router/index.js`
- Modify: `frontend/src/api/index.js`

- [ ] **Step 1: 扩展 App.vue 菜单**

修改 `frontend/src/App.vue`，替换 `<script setup>` 部分:

```vue
<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  DashboardOutlined,
  ProjectOutlined,
  MobileOutlined,
  PlayCircleOutlined,
  KeyOutlined,
  BugOutlined,
  AppstoreOutlined,
  AndroidOutlined,
  CodeOutlined,
  FileTextOutlined,
} from '@ant-design/icons-vue'

const router = useRouter()
const route = useRoute()
const collapsed = ref(false)
const selectedKeys = ref([route.name?.toLowerCase() || 'dashboard'])

const handleMenuClick = ({ key }) => {
  router.push(`/${key}`)
}
</script>
```

替换 `<a-menu>` 内容为 10 个菜单项:

```html
<a-menu v-model:selectedKeys="selectedKeys" theme="dark" mode="inline" @click="handleMenuClick">
  <a-menu-item key="dashboard"><DashboardOutlined /><span>Dashboard</span></a-menu-item>
  <a-menu-item key="projects"><ProjectOutlined /><span>Projects</span></a-menu-item>
  <a-menu-item key="po"><AppstoreOutlined /><span>PO管理</span></a-menu-item>
  <a-menu-item key="apk"><AndroidOutlined /><span>APK管理</span></a-menu-item>
  <a-menu-item key="cases"><FileTextOutlined /><span>测试用例</span></a-menu-item>
  <a-menu-item key="scripts"><CodeOutlined /><span>脚本管理</span></a-menu-item>
  <a-menu-item key="devices"><MobileOutlined /><span>Devices</span></a-menu-item>
  <a-menu-item key="tasks"><PlayCircleOutlined /><span>Tasks</span></a-menu-item>
  <a-menu-item key="keywords"><KeyOutlined /><span>Keywords</span></a-menu-item>
  <a-menu-item key="debug"><BugOutlined /><span>Debug</span></a-menu-item>
</a-menu>
```

- [ ] **Step 2: 扩展路由**

修改 `frontend/src/router/index.js`，增加 4 个 import 和 4 条路由:

Imports 增加:
```javascript
import POManagement from '../views/POManagement.vue'
import APKManagement from '../views/APKManagement.vue'
import TestCaseManagement from '../views/TestCaseManagement.vue'
import ScriptManagement from '../views/ScriptManagement.vue'
```

Routes 增加 (在 `/projects/:id` 之后):
```javascript
{ path: '/po', component: POManagement, name: 'PO' },
{ path: '/apk', component: APKManagement, name: 'APK' },
{ path: '/cases', component: TestCaseManagement, name: 'Cases' },
{ path: '/scripts', component: ScriptManagement, name: 'Scripts' },
```

- [ ] **Step 3: 扩展 API 模块**

修改 `frontend/src/api/index.js`，在 `export default api` 之前增加:

```javascript
// APK Management
export const getApks = (projectId) => api.get(`/api/projects/${projectId}/apks`)
export const uploadApk = (projectId, file, version, description) => {
  const formData = new FormData()
  formData.append('file', file)
  if (version) formData.append('version', version)
  if (description) formData.append('description', description)
  return api.post(`/api/projects/${projectId}/apks`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
export const deleteApk = (projectId, apkId) => api.delete(`/api/projects/${projectId}/apks/${apkId}`)

// Case update/delete
export const updateCase = (projectId, caseId, data) => api.put(`/api/projects/${projectId}/cases/${caseId}`, data)
export const deleteCase = (projectId, caseId) => api.delete(`/api/projects/${projectId}/cases/${caseId}`)

// Device TCP/IP
export const tcpipDevice = (serial, port = 5555) => api.post('/api/devices/tcpip', { serial, port })
export const connectDevice = (ip, port = 5555) => api.post('/api/devices/connect', { ip, port })
export const disconnectDevice = (ip, port = 5555) => api.post('/api/devices/disconnect', { ip, port })

// Element update/delete
export const updateElement = (projectId, pageId, elementId, data) => api.put(`/api/projects/${projectId}/pages/${pageId}/elements/${elementId}`, data)
export const deleteElement = (projectId, pageId, elementId) => api.delete(`/api/projects/${projectId}/pages/${pageId}/elements/${elementId}`)

// Script delete
export const deleteScript = (projectId, scriptId) => api.delete(`/api/projects/${projectId}/scripts/${scriptId}`)
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/App.vue frontend/src/router/index.js frontend/src/api/index.js
git commit -m "feat: expand sidebar to 10 items, add 4 routes, extend API module"
```

---

### Task 4: PO管理页面

**Files:**
- Create: `frontend/src/views/POManagement.vue`

- [ ] **Step 1: 创建 POManagement.vue**

创建 `frontend/src/views/POManagement.vue` — 参见设计文档第4.1节。包含: 项目选择器、PO列表(可展开显示元素)、创建PO弹窗、创建元素弹窗(6种定位方式)、编辑/删除。完整代码见设计文档。

- [ ] **Step 2: Build 验证**

```bash
cd frontend && npm run build
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/POManagement.vue
git commit -m "feat: add PO management page with project selector, PO+Element CRUD"
```

---

### Task 5: APK管理页面

**Files:**
- Create: `frontend/src/views/APKManagement.vue`

- [ ] **Step 1: 创建 APKManagement.vue**

创建 `frontend/src/views/APKManagement.vue` — 参见设计文档第4.2节。包含: 项目选择器、APK版本表格、上传弹窗(拖拽上传+版本号+备注)、删除。完整代码见设计文档。

- [ ] **Step 2: Build 验证**

```bash
cd frontend && npm run build
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/APKManagement.vue
git commit -m "feat: add APK management page with upload, version list, delete"
```

---

### Task 6: 脚本管理页面

**Files:**
- Create: `frontend/src/views/ScriptManagement.vue`

- [ ] **Step 1: 创建 ScriptManagement.vue**

创建 `frontend/src/views/ScriptManagement.vue` — 参见设计文档第4.4节。包含: 项目选择器、脚本表格(可展开显示类/方法)、上传脚本、删除。完整代码见设计文档。

- [ ] **Step 2: Build 验证**

```bash
cd frontend && npm run build
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/ScriptManagement.vue
git commit -m "feat: add script management page with upload, detail expand, delete"
```

---

### Task 7: 测试用例页面（核心：关键字编排）

**Files:**
- Create: `frontend/src/views/TestCaseManagement.vue`

- [ ] **Step 1: 创建 TestCaseManagement.vue**

创建 `frontend/src/views/TestCaseManagement.vue` — 参见设计文档第4.3节，这是最核心最复杂的页面。包含两种模式:

**用例列表模式**: 项目选择器 + 用例表格(名称/类型/步骤数/前置用例/操作) + 创建按钮

**编排模式**: 左栏关键字库(按category分组+搜索+⊕添加按钮) + 右栏步骤编排区(用例名/描述/前置用例下拉框/步骤列表+↑↓排序+×删除/+添加空步骤/保存按钮)。每步可选关键字→动态参数→选元素(按PO分组)。完整代码见设计文档。

- [ ] **Step 2: Build 验证**

```bash
cd frontend && npm run build
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/TestCaseManagement.vue
git commit -m "feat: add test case management with keyword step editor"
```

---

### Task 8: Tasks页面修复

**Files:**
- Modify: `frontend/src/views/Tasks.vue`

- [ ] **Step 1: 重写 Tasks.vue**

完全替换 `frontend/src/views/Tasks.vue` — 参见设计文档第4.5节。包含: 任务表格、创建弹窗(选项目→选用例→选APK版本[含"不安装"选项]→选设备)、执行按钮。完整代码见设计文档。

- [ ] **Step 2: Build 验证**

```bash
cd frontend && npm run build
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/Tasks.vue
git commit -m "feat: rewrite Tasks page with create modal (case, APK, devices)"
```

---

### Task 9: Devices页面增强

**Files:**
- Modify: `frontend/src/views/Devices.vue`

- [ ] **Step 1: 重写 Devices.vue**

完全替换 `frontend/src/views/Devices.vue` — 参见设计文档第4.6节。包含: 设备表格(增加"连接方式"列区分USB/TCP/IP)、扫描按钮、TCP/IP连接按钮→弹窗(选USB设备切换模式+IP/端口连接)、断开按钮。完整代码见设计文档。

- [ ] **Step 2: Build 验证**

```bash
cd frontend && npm run build
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/Devices.vue
git commit -m "feat: enhance Devices page with TCP/IP connect/disconnect"
```

---

### Task 10: 最终整合验证

- [ ] **Step 1: 重建数据库**

```bash
rm -f backend/data/autotest.db
cd backend && python -c "from db.init_db import init_db; init_db()"
```

- [ ] **Step 2: 重建前端**

```bash
cd frontend && npm run build
```

- [ ] **Step 3: 启动后端并验证 API**

```bash
cd backend && python main.py &
sleep 5
curl -s http://localhost:8000/health
curl -s http://localhost:8000/api/projects
curl -s http://localhost:8000/api/keywords
```
Expected: 全部返回 200

- [ ] **Step 4: 端到端验证清单**

访问 http://localhost:8000，逐一验证:
- [ ] 侧边栏显示10个菜单项
- [ ] PO管理: 选项目→创建PO→添加元素→展开查看
- [ ] APK管理: 选项目→上传APK→版本列表显示
- [ ] 测试用例: 选项目→创建用例→关键字编排→保存→列表显示
- [ ] 脚本管理: 选项目→上传脚本→展开查看类方法
- [ ] Devices: 扫描→TCP/IP弹窗可用
- [ ] Tasks: 创建弹窗→选用例/APK/设备→创建

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "feat: complete frontend feature set - PO, APK, cases, scripts, TCP/IP, task creation"
```