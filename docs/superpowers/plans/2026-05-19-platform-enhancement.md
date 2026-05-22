# MultiUiAutoTest 平台增强实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实施 9 个平台增强需求：异步任务执行、报告管理、项目详情页改造、用例 type 字段移除、PO 跨项目复制、APK 包名解析、脚本管理优化、设备 IP 多方法探测、任务管理交互重构、关键字弹窗优化

**Architecture:**
- Phase 1: 异步任务执行（后台线程池）+ 报告管理（数据库存储自包含 HTML）
- Phase 2: 独立前端改造（6 个页面/组件优化）
- Phase 3: 后端工具函数优化（设备 IP 获取、APK 解析）

**Tech Stack:** Python FastAPI, SQLAlchemy, ThreadPoolExecutor, WebSocket, Vue3, WeasyPrint

---

## 文件结构总览

### 后端新增文件
- `backend/models/report.py` — 报告模型（content 字段存自包含 HTML）
- `backend/schemas/report.py` — 报告 schema
- `backend/api/reports.py` — 报告 API 路由
- `backend/core/report_generator.py` — HTML/PDF 报告生成器
- `backend/tests/test_reports.py` — 报告 API 测试
- `backend/tests/test_async_tasks.py` — 异步任务测试

### 后端修改文件
- `backend/api/tasks.py` — execute_task 改为异步返回 + 报告 API
- `backend/core/task_dispatcher.py` — 后台线程执行 + 并发管理器
- `backend/api/__init__.py` — 注册 reports 路由
- `backend/api/projects.py` — 新增 copy-from 接口
- `backend/api/pages.py` — 新增 copy-from 接口
- `backend/api/apks.py` — APK 解析包名+版本号
- `backend/api/scripts.py` — 新增全局列表接口 + 修复上传
- `backend/api/devices.py` — 多方法 IP 获取
- `backend/models/test_case.py` — type 默认 keyword
- `backend/schemas/test_case.py` — 去掉 type 可选
- `backend/db/init_db.py` — 新增 reports 表

### 前端修改文件
- `frontend/src/App.vue` — 侧边栏增加"报告管理"
- `frontend/src/api/index.js` — 新增报告、复制页面、全局脚本等 API
- `frontend/src/views/Reports.vue` — 新增报告管理页面
- `frontend/src/views/ProjectDetail.vue` — 改为纯查看+跳转
- `frontend/src/views/TestCaseManagement.vue` — 去掉 type
- `frontend/src/views/POManagement.vue` — 复制功能 + 全项目展示
- `frontend/src/views/APKManagement.vue` — 包名+版本合并列
- `frontend/src/views/ScriptManagement.vue` — 全项目展示 + 修复
- `frontend/src/views/Tasks.vue` — 交互重构
- `frontend/src/views/Keywords.vue` — 弹窗缩小 + 示例

### 前端新增文件
- `frontend/src/views/Reports.vue`

---

## Phase 1: 异步任务执行 + 报告管理

### Task 1: Report 数据模型与 Schema

**Files:**
- Create: `backend/models/report.py`
- Create: `backend/schemas/report.py`
- Modify: `backend/db/init_db.py` (添加 reports 表)

- [ ] **Step 1: 创建 Report 模型**

```python
# backend/models/report.py
import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from db.database import Base
from datetime import datetime

def utc_now():
    return datetime.utcnow()

class Report(Base):
    __tablename__ = "reports"
    id = Column(String, primary_key=True, default=lambda: f"rpt_{uuid.uuid4().hex[:8]}")
    task_id = Column(String, ForeignKey("test_tasks.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now)
```

- [ ] **Step 2: 创建 Report Schema**

```python
# backend/schemas/report.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ReportResponse(BaseModel):
    id: str
    task_id: str
    content: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ReportMetadata(BaseModel):
    id: str
    task_id: str
    created_at: datetime

    class Config:
        from_attributes = True
```

- [ ] **Step 3: 在 init_db.py 添加 reports 表**

```python
# backend/db/init_db.py
from models.report import Report  # 添加这行
# 在 init_db 函数中添加: Base.metadata.create_all(bind=engine)
```

- [ ] **Step 4: 提交**

```bash
git add backend/models/report.py backend/schemas/report.py backend/db/init_db.py
git commit -m "feat: add Report model and schema"
```

---

### Task 2: ReportGenerator 报告生成器

**Files:**
- Create: `backend/core/report_generator.py`
- Test: `backend/tests/test_reports.py`

- [ ] **Step 1: 创建 ReportGenerator 模块**

```python
# backend/core/report_generator.py
from typing import Dict, List, Optional
from datetime import datetime
import base64
import os

class ReportGenerator:
    def __init__(self, task_data: Dict, results: List[Dict], logs: List[Dict]):
        self.task_data = task_data
        self.results = results
        self.logs = logs

    def generate_html(self) -> str:
        passed = sum(1 for r in self.results if r.get('status') == 'passed')
        failed = sum(1 for r in self.results if r.get('status') == 'failed')
        total = len(self.results)

        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>测试报告 - {self.task_data.get('name', 'Unknown')}</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; }}
.summary {{ background: #f5f5f5; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
.passed {{ color: #52c41a; }} .failed {{ color: #ff4d4f; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
th {{ background: #fafafa; }} .log-entry {{ font-family: monospace; font-size: 12px; padding: 4px 8px; }}
</style>
</head>
<body>
<h1>测试报告</h1>
<div class="summary">
  <h2>执行概览</h2>
  <p>任务: {self.task_data.get('name', 'N/A')}</p>
  <p>状态: <span class="{'passed' if failed == 0 else 'failed'}">{self.task_data.get('status', 'N/A')}</span></p>
  <p>通过: <span class="passed">{passed}/{total}</span> | 失败: <span class="failed">{failed}/{total}</span></p>
  <p>时间: {self.task_data.get('created_at', 'N/A')}</p>
</div>
<h3>设备结果</h3>
<table>
<tr><th>设备</th><th>状态</th><th>开始时间</th><th>结束时间</th></tr>
{''.join(f"<tr><td>{r.get('device_id', 'N/A')}</td><td>{r.get('status', 'N/A')}</td><td>{r.get('start_time', 'N/A')}</td><td>{r.get('end_time', 'N/A')}</td></tr>" for r in self.results)}
</table>
<h3>执行日志</h3>
<div class="logs">
{''.join(f"<div class='log-entry'>[{log.get('timestamp', '')}] {log.get('level', 'INFO')}: {log.get('message', '')}</div>" for log in self.logs)}
</div>
</body>
</html>"""
        return html

    def generate_pdf(self) -> bytes:
        from weasyprint import HTML
        html_content = self.generate_html()
        pdf_io = HTML(string=html_content).write_pdf()
        return pdf_io
```

- [ ] **Step 2: 编写测试**

```python
# backend/tests/test_reports.py
from core.report_generator import ReportGenerator

def test_report_generator_html():
    task_data = {'name': 'Test Task', 'status': 'completed', 'created_at': '2026-05-19 10:00:00'}
    results = [{'device_id': 'device1', 'status': 'passed', 'start_time': '10:00', 'end_time': '10:05'}]
    logs = [{'timestamp': '10:00', 'level': 'INFO', 'message': 'Test started'}]

    generator = ReportGenerator(task_data, results, logs)
    html = generator.generate_html()

    assert 'Test Task' in html
    assert '1/1' in html or 'passed' in html.lower()
    assert '<!DOCTYPE html>' in html
```

- [ ] **Step 3: 运行测试**

Run: `cd backend && python -m pytest tests/test_reports.py -v`
Expected: PASS

- [ ] **Step 4: 提交**

```bash
git add backend/core/report_generator.py backend/tests/test_reports.py
git commit -m "feat: add ReportGenerator for HTML/PDF report generation"
```

---

### Task 3: 异步任务执行

**Files:**
- Modify: `backend/core/task_dispatcher.py`
- Modify: `backend/api/tasks.py`
- Test: `backend/tests/test_async_tasks.py`

- [ ] **Step 1: 修改 TaskDispatcher 支持后台执行**

```python
# backend/core/task_dispatcher.py
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
import logging

logger = logging.getLogger("autotest")

class TaskDispatcher:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.running_tasks = {}

    def dispatch(self, task_id: str, db):
        """立即返回，后台线程执行"""
        future = self.executor.submit(self._execute_task, task_id, db)
        self.running_tasks[task_id] = future
        return "started"

    def _execute_task(self, task_id: str, db):
        """实际执行逻辑（内部调用）"""
        # 原有的 execute_task 逻辑移到这里
        from models.test_task import TestTask
        from models.task_result import TaskResult

        task = db.query(TestTask).filter(TestTask.id == task_id).first()
        if not task:
            logger.error(f"Task {task_id} not found")
            return

        task.status = "running"
        db.commit()

        # 执行测试逻辑...
        # 完成后更新状态
        task.status = "completed"
        db.commit()

    def get_status(self, task_id: str) -> Optional[str]:
        if task_id in self.running_tasks:
            future = self.running_tasks[task_id]
            if future.done():
                return "completed"
            return "running"
        return None
```

- [ ] **Step 2: 修改 execute_task API**

```python
# backend/api/tasks.py - execute_task 端点改为:
@router.post("/tasks/{task_id}/execute")
def execute_task(task_id: str, db: Session = Depends(get_db)):
    """Execute a test task on all assigned devices - returns immediately."""
    task = db.query(TestTask).filter(TestTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status == "running":
        raise HTTPException(status_code=400, detail="Task is already running")

    task.status = "running"
    db.commit()

    # 后台线程执行，不阻塞 API
    threading.Thread(target=task_dispatcher._execute_task, args=(task_id, db)).start()

    return {"task_id": task_id, "status": "running", "message": "Task started in background"}
```

- [ ] **Step 3: 编写异步任务测试**

```python
# backend/tests/test_async_tasks.py
def test_execute_task_returns_immediately():
    # 验证 API 立即返回，不等待任务完成
    response = client.post("/api/tasks/1/execute")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert "started" in data.get("message", "").lower()
```

- [ ] **Step 4: 运行测试**

Run: `cd backend && python -m pytest tests/test_async_tasks.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend/core/task_dispatcher.py backend/api/tasks.py backend/tests/test_async_tasks.py
git commit -m "feat: implement async task execution with background thread pool"
```

---

### Task 4: 报告 API 端点

**Files:**
- Create: `backend/api/reports.py`
- Modify: `backend/api/__init__.py`

- [ ] **Step 1: 创建报告 API**

```python
# backend/api/reports.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from db.database import get_db
from models.report import Report
from schemas.report import ReportResponse, ReportMetadata
from core.report_generator import ReportGenerator
from models.test_task import TestTask
from models.task_result import TaskResult
import json

router = APIRouter(prefix="/api", tags=["reports"])

@router.get("/reports", response_model=list[ReportMetadata])
def list_reports(db: Session = Depends(get_db)):
    reports = db.query(Report).all()
    return reports

@router.get("/tasks/{task_id}/report")
def get_task_report(task_id: str, db: Session = Depends(get_db)):
    task = db.query(TestTask).filter(TestTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    report = db.query(Report).filter(Report.task_id == task_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return Response(content=report.content, media_type="text/html")

@router.get("/tasks/{task_id}/report/download")
def download_report(task_id: str, format: str = "html", db: Session = Depends(get_db)):
    task = db.query(TestTask).filter(TestTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    report = db.query(Report).filter(Report.task_id == task_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if format == "pdf":
        from weasyprint import HTML
        pdf_bytes = HTML(string=report.content).write_pdf()
        return Response(content=pdf_bytes, media_type="application/pdf",
                        headers={"Content-Disposition": f"attachment; filename=report_{task_id}.pdf"})

    return Response(content=report.content, media_type="text/html",
                    headers={"Content-Disposition": f"attachment; filename=report_{task_id}.html"})

def generate_and_save_report(task_id: str, db: Session):
    task = db.query(TestTask).filter(TestTask.id == task_id).first()
    results = db.query(TaskResult).filter(TaskResult.task_id == task_id).all()

    results_data = [{
        "device_id": r.device_id,
        "status": r.status,
        "start_time": r.start_time.isoformat() if r.start_time else None,
        "end_time": r.end_time.isoformat() if r.end_time else None,
    } for r in results]

    task_data = {
        "name": f"Task {task_id}",
        "status": task.status,
        "created_at": task.created_at.isoformat() if task.created_at else None,
    }

    generator = ReportGenerator(task_data, results_data, [])
    html_content = generator.generate_html()

    report = Report(task_id=task_id, content=html_content)
    db.add(report)
    db.commit()
```

- [ ] **Step 2: 注册路由**

```python
# backend/api/__init__.py
from api.reports import router as reports_router

api_router.include_router(reports_router)
```

- [ ] **Step 3: 提交**

```bash
git add backend/api/reports.py backend/api/__init__.py
git commit -m "feat: add report API endpoints"
```

---

### Task 5: 前端 Reports 页面

**Files:**
- Create: `frontend/src/views/Reports.vue`
- Modify: `frontend/src/App.vue` (侧边栏添加菜单)
- Modify: `frontend/src/api/index.js`

- [ ] **Step 1: 添加报告 API**

```javascript
// frontend/src/api/index.js
export const getReports = () => api.get('/api/reports')
export const getTaskReport = (taskId) => api.get(`/api/tasks/${taskId}/report`)
export const downloadReport = (taskId, format) => api.get(`/api/tasks/${taskId}/report/download?format=${format}`, {
  responseType: format === 'pdf' ? 'blob' : 'text',
})
```

- [ ] **Step 2: 创建 Reports.vue**

```vue
<!-- frontend/src/views/Reports.vue -->
<template>
  <div class="reports-container">
    <h1>报告管理</h1>
    <a-table :columns="columns" :data-source="reports" row-key="id">
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'action'">
          <a-button type="link" @click="viewReport(record.task_id)">查看</a-button>
          <a-button type="link" @click="downloadHtml(record.task_id)">HTML</a-button>
          <a-button type="link" @click="downloadPdf(record.task_id)">PDF</a-button>
        </template>
      </template>
    </a-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getReports, downloadReport } from '@/api'

const reports = ref([])
const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id' },
  { title: '任务ID', dataIndex: 'task_id', key: 'task_id' },
  { title: '创建时间', dataIndex: 'created_at', key: 'created_at' },
  { title: '操作', key: 'action' },
]

onMounted(async () => {
  const res = await getReports()
  reports.value = res.data
})

const viewReport = (taskId) => {
  window.open(`/api/tasks/${taskId}/report`, '_blank')
}

const downloadHtml = (taskId) => {
  window.location.href = `/api/tasks/${taskId}/report/download?format=html`
}

const downloadPdf = (taskId) => {
  window.location.href = `/api/tasks/${taskId}/report/download?format=pdf`
}
</script>
```

- [ ] **Step 3: 在 App.vue 侧边栏添加菜单**

```vue
<!-- 在侧边栏菜单中添加 -->
<router-link to="/reports">
  <a-menu-item key="reports">
    <template #icon><FileTextOutlined /></template>
    报告管理
  </a-menu-item>
</router-link>
```

- [ ] **Step 4: 在 router/index.js 添加路由**

```javascript
// frontend/src/router/index.js
import Reports from '@/views/Reports.vue'

{
  path: '/reports',
  name: 'Reports',
  component: Reports,
}
```

- [ ] **Step 5: 提交**

```bash
git add frontend/src/views/Reports.vue frontend/src/App.vue frontend/src/api/index.js frontend/src/router/index.js
git commit -m "feat: add Reports page and navigation"
```

---

## Phase 2: 后端独立功能改造

### Task 6: 用例管理去掉 type 字段

**Files:**
- Modify: `backend/models/test_case.py`
- Modify: `backend/schemas/test_case.py`
- Modify: `frontend/src/views/TestCaseManagement.vue`
- Modify: `frontend/src/views/Tasks.vue`

- [ ] **Step 1: 修改 TestCase 模型**

```python
# backend/models/test_case.py
# 找到 type 字段，添加默认值
type = Column(String, default="keyword")  # 不再 nullable=False，默认为 keyword
```

- [ ] **Step 2: 修改 TestCaseCreate Schema**

```python
# backend/schemas/test_case.py
class TestCaseCreate(BaseModel):
    name: str
    project_id: str
    steps: list[dict] = []
    pre_case_id: Optional[str] = None
    # 删除 type 字段，自动填充为 "keyword"
```

- [ ] **Step 3: 修改前端 TestCaseManagement.vue**

```vue
<!-- 删除用例类型的 <a-select> 和类型列 -->
<!-- 找到并删除类似以下代码: -->
<a-select v-model:value="caseType">
  <a-select-option value="keyword">关键字驱动</a-select-option>
</a-select>
```

- [ ] **Step 4: 修改 Tasks.vue 创建任务弹窗**

```vue
<!-- 删除用例类型的区分选项 -->
```

- [ ] **Step 5: 提交**

```bash
git add backend/models/test_case.py backend/schemas/test_case.py
git add frontend/src/views/TestCaseManagement.vue frontend/src/views/Tasks.vue
git commit -m "refactor: remove type field from test case management"
```

---

### Task 7: PO 跨项目复制

**Files:**
- Modify: `backend/api/projects.py`
- Modify: `backend/api/pages.py`
- Modify: `frontend/src/api/index.js`
- Modify: `frontend/src/views/POManagement.vue`

- [ ] **Step 1: 在 pages.py 添加复制接口**

```python
# backend/api/pages.py
@router.post("/projects/{project_id}/pages/copy-from")
def copy_page_from_source(project_id: str, source_page_id: str, db: Session = Depends(get_db)):
    source_page = db.query(Page).filter(Page.id == source_page_id).first()
    if not source_page:
        raise HTTPException(status_code=404, detail="Source page not found")

    new_page = Page(
        project_id=project_id,
        name=source_page.name + "_copy",
        description=source_page.description,
    )
    db.add(new_page)
    db.flush()

    # 复制元素
    from models.element import Element
    source_elements = db.query(Element).filter(Element.page_id == source_page_id).all()
    for elem in source_elements:
        new_elem = Element(
            page_id=new_page.id,
            name=elem.name,
            locator_type=elem.locator_type,
            locator_value=elem.locator_value,
            action=elem.action,
        )
        db.add(new_elem)

    db.commit()
    db.refresh(new_page)
    return new_page
```

- [ ] **Step 2: 添加前端 API**

```javascript
// frontend/src/api/index.js
export const copyPage = (projectId, sourcePageId) =>
  api.post(`/api/projects/${projectId}/pages/copy-from`, { source_page_id: sourcePageId })
```

- [ ] **Step 3: 修改 POManagement.vue**

```vue
<!-- 添加复制按钮和弹窗 -->
<a-button @click="showCopyDialog">从其他项目复制</a-button>

<!-- 复制弹窗内容 -->
<a-modal v-model:open="copyDialogVisible" title="复制页面" @ok="handleCopy">
  <a-select v-model:value="sourceProjectId" placeholder="选择源项目">
    <a-select-option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</a-select-option>
  </a-select>
  <a-select v-model:value="sourcePageId" placeholder="选择源页面">
    <a-select-option v-for="pg in sourcePages" :key="pg.id" :value="pg.id">{{ pg.name }}</a-select-option>
  </a-select>
</a-modal>
```

- [ ] **Step 4: 提交**

```bash
git add backend/api/pages.py frontend/src/api/index.js frontend/src/views/POManagement.vue
git commit -m "feat: add cross-project page copy functionality"
```

---

### Task 8: APK 包名解析

**Files:**
- Modify: `backend/api/apks.py`
- Modify: `frontend/src/views/APKManagement.vue`

- [ ] **Step 1: 修改 APK 上传逻辑**

```python
# backend/api/apks.py
import subprocess
import re

def parse_apk_info(apk_path: str) -> tuple[str, str]:
    """使用 aapt 解析 APK 包名和版本号"""
    try:
        result = subprocess.run(
            ["aapt", "dump", "badging", apk_path],
            capture_output=True, text=True, timeout=10
        )
        output = result.stdout

        package_match = re.search(r"package: name='([^']+)'", output)
        version_match = re.search(r"versionName='([^']+)'", output)

        package_name = package_match.group(1) if package_match else "unknown"
        version = version_match.group(1) if version_match else "unknown"

        return package_name, version
    except Exception as e:
        logging.warning(f"aapt parse failed: {e}")
        return "unknown", "unknown"

# 在上传 API 中调用
@router.post("/projects/{project_id}/apks")
async def upload_apk(project_id: str, file: UploadFile = File(...), ...):
    # ... 文件保存逻辑 ...

    package_name, version = parse_apk_info(file_path)

    apk = APKModel(package_name=package_name, version=version, ...)
```

- [ ] **Step 2: 修改前端显示**

```vue
<!-- frontend/src/views/APKManagement.vue -->
<!-- 将包名和版本合并为一列 -->
<a-table-column title="包名" dataIndex="package_name">
  <template #default="{ record }">
    {{ record.package_name }} v{{ record.version }}
  </template>
</a-table-column>
```

- [ ] **Step 3: 提交**

```bash
git add backend/api/apks.py frontend/src/views/APKManagement.vue
git commit -m "feat: parse APK package name and version on upload"
```

---

### Task 9: 脚本管理优化 + 500 修复

**Files:**
- Modify: `backend/api/scripts.py`
- Modify: `frontend/src/views/ScriptManagement.vue`
- Modify: `frontend/src/api/index.js`

- [ ] **Step 1: 添加全局脚本列表 API**

```python
# backend/api/scripts.py
@router.get("/scripts")
def list_all_scripts(db: Session = Depends(get_db)):
    scripts = db.query(Script).all()
    result = []
    for s in scripts:
        project = db.query(Project).filter(Project.id == s.project_id).first()
        result.append({
            "id": s.id,
            "name": s.name,
            "path": s.path,
            "project_id": s.project_id,
            "project_name": project.name if project else "Unknown",
        })
    return result
```

- [ ] **Step 2: 修复上传 500 错误**

```python
# 检查并修复上传逻辑，确保错误处理完整
@router.post("/projects/{project_id}/scripts")
async def upload_script(project_id: str, file: UploadFile = File(...)):
    try:
        # ... 文件保存逻辑 ...
        # 提取类名和方法名，增加异常捕获
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            classes = re.findall(r'class (\w+)', content)
        except Exception as e:
            logging.error(f"Failed to parse script: {e}")
            classes = []

        script = Script(project_id=project_id, name=file.filename, path=str(file_path))
        db.add(script)
        db.commit()
        return script
    except Exception as e:
        logging.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

- [ ] **Step 3: 前端改造**

```vue
<!-- ScriptManagement.vue -->
<!-- 默认加载所有项目脚本 -->
<script setup>
const scripts = ref([])
const selectedProject = ref(null)

const loadScripts = async () => {
  const res = await getScripts(selectedProject.value)
  scripts.value = res.data
}
</script>
```

- [ ] **Step 4: 添加 API**

```javascript
// frontend/src/api/index.js
export const getScripts = (projectId) =>
  projectId ? api.get(`/api/projects/${projectId}/scripts`) : api.get('/api/scripts')
```

- [ ] **Step 5: 提交**

```bash
git add backend/api/scripts.py frontend/src/views/ScriptManagement.vue frontend/src/api/index.js
git commit -m "feat: add global script list API and fix upload error"
```

---

### Task 10: 设备 IP 多方法探测

**Files:**
- Modify: `backend/api/devices.py`

- [ ] **Step 1: 添加 get_device_ip 函数**

```python
# backend/api/devices.py
import re
import subprocess

def get_device_ip(serial: str) -> str:
    """使用多种方法获取设备 IP"""
    methods = [
        f"adb -s {serial} shell ip addr show wlan0",
        f"adb -s {serial} shell ifconfig wlan0",
        f"adb -s {serial} shell getprop dhcp.wlan0.ipaddress",
    ]
    for method in methods:
        try:
            result = subprocess.run(method.split(), capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout:
                ip_match = re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', result.stdout)
                if ip_match:
                    ip = ip_match.group()
                    if not ip.startswith('127.') and not ip.startswith('169.254.'):
                        return ip
        except Exception:
            continue
    return None

# 替换 connect_device_one_click 中的 IP 获取逻辑
```

- [ ] **Step 2: 提交**

```bash
git add backend/api/devices.py
git commit -m "feat: add multi-method device IP detection"
```

---

## Phase 3: 前端页面交互改造

### Task 11: 项目详情页改为纯查看 + 跳转

**Files:**
- Modify: `frontend/src/views/ProjectDetail.vue`

- [ ] **Step 1: 改造 ProjectDetail.vue**

删除所有 Modal（添加页面、添加用例）和新增按钮，改为纯展示 + 跳转链接：

```vue
<!-- 页面 tab -->
<a-tab-pane key="pages" tab="页面">
  <a-table :columns="pageColumns" :data-source="pages">
    <template #bodyCell="{ column, record }">
      <template v-if="column.key === 'action'">
        <router-link :to="`/po?page=${record.id}`">→ PO管理</router-link>
      </template>
    </template>
  </a-table>
</a-tab-pane>

<!-- 用例 tab -->
<a-tab-pane key="cases" tab="用例">
  <a-table :columns="caseColumns" :data-source="cases">
    <template #bodyCell="{ column, record }">
      <template v-if="column.key === 'action'">
        <router-link :to="`/cases?case=${record.id}`">→ 用例管理</router-link>
      </template>
    </template>
  </a-table>
</a-tab-pane>

<!-- 脚本 tab -->
<a-tab-pane key="scripts" tab="脚本">
  <a-table :columns="scriptColumns" :data-source="scripts">
    <template #bodyCell="{ column, record }">
      <template v-if="column.key === 'action'">
        <router-link :to="`/scripts?script=${record.id}`">→ 脚本管理</router-link>
      </template>
    </template>
  </a-table>
</a-tab-pane>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/views/ProjectDetail.vue
git commit -m "refactor: convert ProjectDetail to read-only with navigation links"
```

---

### Task 12: 任务管理交互重构

**Files:**
- Modify: `frontend/src/views/Tasks.vue`

- [ ] **Step 1: 重构任务列表和创建弹窗**

```vue
<!-- 任务列表列 -->
const columns = [
  { title: 'ID', dataIndex: 'id' },
  { title: '用例/脚本', dataIndex: 'name' },
  { title: '类型', dataIndex: 'type' },
  { title: 'APK', dataIndex: 'apk' },
  { title: '状态', dataIndex: 'status' },
  { title: '创建时间', dataIndex: 'created_at' },
  { title: '操作', key: 'action' },
]

<!-- 创建弹窗 -->
<a-modal v-model:open="createVisible" title="创建任务">
  <a-form>
    <a-form-item label="测试内容">
      <a-select v-model:value="taskForm.case_or_script_id">
        <a-optgroup label="用例">
          <a-select-option v-for="c in cases" :key="c.id" :value="`case:${c.id}`">{{ c.name }}</a-select-option>
        </a-optgroup>
        <a-optgroup label="脚本">
          <a-select-option v-for="s in scripts" :key="s.id" :value="`script:${s.id}`">{{ s.name }}</a-select-option>
        </a-optgroup>
      </a-select>
    </a-form-item>
    <a-form-item label="APK版本">
      <a-select v-model:value="taskForm.apk_id">
        <a-select-option v-for="a in apks" :key="a.id" :value="a.id">
          {{ a.package_name }} v{{ a.version }}
        </a-select-option>
      </a-select>
    </a-form-item>
  </a-form>
</a-modal>

<!-- 执行后显示"查看报告"按钮 -->
<template #action="{ record }">
  <a-button v-if="record.status === 'completed'" type="link" @click="viewReport(record.id)">查看报告</a-button>
  <a-button v-else type="primary" @click="executeTask(record.id)">执行</a-button>
</template>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/views/Tasks.vue
git commit -m "refactor: redesign task management UI with case/script selection"
```

---

### Task 13: 关键字弹窗优化

**Files:**
- Modify: `frontend/src/views/Keywords.vue`

- [ ] **Step 1: 缩小弹窗宽度 + 添加示例**

```vue
<a-modal
  v-model:open="editVisible"
  title="编辑关键字"
  :width="500"
>
  <a-form>
    <a-textarea v-model:value="keywordForm.code" :rows="10" />
  </a-form>

  <template #footer>
    <div class="example-section">
      <h4>示例参考</h4>
      <pre class="example-code">{{ exampleCode }}</pre>
    </div>
  </template>
</a-modal>

<script setup>
const exampleCode = `click("id=btn_submit")
wait(2)
input_text("id=input_name", "testuser")
screenshot()`
</script>

<style scoped>
.example-section {
  text-align: left;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #eee;
}
.example-code {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  font-size: 12px;
  color: #666;
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/views/Keywords.vue
git commit -m "feat: optimize keyword dialog with smaller width and example"
```

---

## 验证与测试

### 整体验证步骤

- [ ] **Step 1: 运行所有后端测试**

Run: `cd backend && python -m pytest tests/ -v --tb=short`
Expected: 所有测试通过

- [ ] **Step 2: 启动后端验证 API**

Run: `cd backend && python main.py`
验证 WebSocket 端点: `ws://localhost:8000/ws/tasks/{id}/logs`

- [ ] **Step 3: 启动前端验证页面**

Run: `cd frontend && npm run dev`
验证所有页面正常加载

---

## 实施顺序建议

1. **Phase 1** (Task 1-5): 异步任务执行 + 报告管理（基础功能）
2. **Phase 2** (Task 6-10): 后端独立功能改造
3. **Phase 3** (Task 11-13): 前端页面交互改造

---

*计划完成于 2026-05-19*
