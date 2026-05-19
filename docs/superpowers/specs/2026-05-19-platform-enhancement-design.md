# MultiUiAutoTest 平台增强设计规格

> **日期**: 2026-05-19
> **状态**: 待审核
> **范围**: 9 个需求的统一设计与实施规划

---

## 1. 任务异步执行 + 报告管理

### 1.1 异步任务执行

**当前问题**: `execute_task` API 同步阻塞，任务 A 执行期间无法创建/启动任务 B。

**改造方案**: 后台线程池并发执行。

- `TaskDispatcher.dispatch()` 从 API 直接调用改为后台线程启动：`threading.Thread(target=dispatcher.dispatch, args=(task_id,)).start()`
- API `POST /tasks/{id}/execute` 立即返回 `{task_id, status: "running"}`，不再等待执行完成
- 新增全局线程池管理器，多个任务可同时并发执行，每个任务内部再为每台设备开子线程并发执行
- 任务状态流转：`pending → running → completed/failed`

**并发模型**:

```
┌─────────── API ───────────┐
│ POST /tasks/1/execute      │ → 立即返回 {status:running}
│ POST /tasks/2/execute      │ → 立即返回 {status:running}
└─────────────────────────────┘
        ↓ 后台线程池
┌─── ThreadPoolExecutor ─────┐
│ Task1: Device1 | Device2 | Device3 │
│ Task2: Device4 | Device5           │
└────────────────────────────────────┘
        ↓ WebSocket 推送
┌─── 前端实时进度 ──────────┐
│ 任务1进度 | 任务2进度      │
└─────────────────────────────┘
```

### 1.2 报告生成

- 新增 `ReportGenerator` 模块：任务完成后自动生成报告
- 报告内容：通过/失败统计、每步骤执行日志、设备信息、执行时间、用例名称
- 报告格式：HTML（平台内查看，任务完成时自动生成）+ PDF（下载时按需生成，使用 `weasyprint` 转换）
- 报告存储：`reports/{task_id}/report.html`（自动生成），PDF 按需生成后缓存在同目录

### 1.3 报告数据模型

```python
class Report(Base):
    __tablename__ = "reports"
    id = Column(String, primary_key=True, default=lambda: f"rpt_{uuid.uuid4().hex[:8]}")
    task_id = Column(String, ForeignKey("test_tasks.id"), nullable=False)
    html_path = Column(String, nullable=False)
    pdf_path = Column(String)
    created_at = Column(DateTime, default=utc_now)
```

### 1.4 报告 API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/tasks/{id}/report` | GET | 查看报告 HTML |
| `/api/tasks/{id}/report/download?format=pdf|html` | GET | 下载报告文件 |
| `/api/reports` | GET | 报告列表 |

### 1.5 前端改动

- 前端新增 `Reports.vue` 页面，侧边栏菜单加入"报告管理"
- 报告列表展示：任务名称、类型、状态、创建时间、操作（查看/下载）
- Tasks.vue：执行按钮点击后状态立即变为 `running`，任务完成后显示"查看报告"按钮
- 通过已有 WebSocket `/ws/tasks/{id}/logs` 接收实时进度

---

## 2. 项目详情页纯查看 + 跳转

### 2.1 改造说明

当前 ProjectDetail.vue 有"添加页面"、"添加用例"、"上传脚本"的入口和 Modal。改为纯查看 + 跳转。

**新交互**:
- 标题区域展示项目信息 + 统计卡片（页面数、用例数、脚本数）
- 页面 tab：只展示页面列表（名称、描述、元素数），每行有"→ PO管理"跳转链接
- 用例 tab：只展示用例列表（名称、步骤数、前置用例），每行有"→ 用例管理"跳转链接
- 脚本 tab：只展示脚本列表（名称、文件路径），每行有"→ 脚本管理"跳转链接
- 删除所有 Modal（添加页面、添加用例）和新增按钮

---

## 3. 用例管理去掉 type 字段

### 3.1 改造说明

当前 TestCase 模型有 `type` 字段（"keyword" / "script"），实际只有关键字驱动在用。

**后端**:
- `TestCase` 模型：`type` 字段默认值 `"keyword"`，不再暴露给前端选择
- `TestCaseCreate` schema：去掉 `type` 可选字段，自动填充 `"keyword"`

**前端**:
- TestCaseManagement.vue：删除用例类型的 `<a-select>` 和类型列
- Tasks.vue：任务创建弹窗中不再区分"脚本驱动"类型用例

---

## 4. PO 跨项目复制

### 4.1 复制功能

当前 POManagement.vue 只能创建新页面，需增加跨项目复制。

**后端新增 API**:
- `POST /api/projects/{project_id}/pages/copy-from`，接收 `{source_page_id}`
- 复制源页面及所有元素到目标项目，生成新 ID，完全独立

**前端改动**:
- POManagement.vue：新增"从其他项目复制"按钮
- 弹窗流程：选择源项目 → 选择源页面 → 确认复制
- POManagement 默认展示所有项目的页面（每行带项目名标签），顶部有项目筛选下拉框

---

## 5. APK 包名解析

### 5.1 自动解析

当前上传 APK 时 `package_name` 和 `version` 没有正确解析。

**后端改造**:
- 上传后调用 `aapt dump badging <apk_path>` 提取 `package_name` 和 `version_name`
- 如果没有 aapt 命令，使用 Python `androguard` 库解析 APK 元信息作为备选
- 自动填充到 APKPackage 模型的 `package_name` 和 `version` 字段

**前端改动**:
- APKManagement.vue：表格合并为"包名+版本号"单列（如 `com.example.app v1.2.3`）
- 任务创建弹窗 APK 选择项也显示"包名 v版本号"

---

## 6. 脚本管理 - 全项目展示 + 上传 500 修复

### 6.1 全项目展示

**前端改动**:
- ScriptManagement.vue 默认不选项目，直接加载所有项目脚本
- 每行带项目名标签（如 `[项目A] test_login.py`）
- 顶部有项目筛选下拉框可过滤
- 上传脚本时需先选择目标项目

**后端新增 API**:
- `GET /api/scripts` 全局脚本列表（返回所有脚本，每个带 `project_id` 和 `project_name`）

### 6.2 上传 500 修复

排查当前上传脚本 500 错误：
- 检查文件保存路径、脚本解析逻辑
- 确保文件写入和类/方法提取不报错
- 增加错误处理和日志

---

## 7. 设备 IP 获取 - 多方法探测

### 7.1 改造说明

当前只用 `ip route` 获取设备 IP，经常失败。改用 4 种方法依次探测。

**新增 `get_device_ip(serial)` 函数**:

```python
def get_device_ip(serial):
    ip_methods = [
        f"adb -s {serial} shell ip addr show wlan0",
        f"adb -s {serial} shell ifconfig wlan0",
        f"adb -s {serial} shell getprop dhcp.wlan0.ipaddress",
        f"adb -s {serial} shell getprop net.dns1",
    ]
    for method in ip_methods:
        result = subprocess.run(method.split(), capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout:
            ip_match = re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', result.stdout)
            if ip_match:
                ip = ip_match.group()
                if not ip.startswith('127.') and not ip.startswith('169.254.'):
                    return ip
    return None
```

替换 `connect_device_one_click` 中的 IP 获取逻辑，使用此函数。获取到 IP 后再执行 `adb connect`。

---

## 8. 任务管理交互重构

### 8.1 任务列表

改为显示：ID、用例/脚本名称、类型标签（用例/脚本）、APK 包名+版本号、状态、创建时间、操作（执行/查看报告）。

### 8.2 创建任务弹窗

- "测试内容" → "选择测试用例或脚本"，分组下拉（用例组/脚本组）
- "APK版本" → "APK包名+版本号"，每项显示 `包名 v版本号`
- 任务名称：用例任务显示用例名，脚本任务显示脚本名，类型用颜色标签区分

---

## 9. 关键字弹窗优化

### 9.1 改造说明

- 弹窗宽度从 700px 缩小为 500px
- 在代码编辑区下方增加"示例参考"区域
- 展示一个内置关键字（如 `click`）的代码片段作为参考
- 示例代码只读、灰色显示，不生效

---

## 文件结构总览

### 后端新增文件
- `backend/models/report.py` — 报告模型
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
- `frontend/src/views/Devices.vue` — （无改动，后端 IP 修复即可）
- `frontend/src/views/Tasks.vue` — 交互重构
- `frontend/src/views/Keywords.vue` — 弹窗缩小 + 示例

### 前端新增文件
- `frontend/src/views/Reports.vue`

---

*设计文档生成于 2026-05-19*