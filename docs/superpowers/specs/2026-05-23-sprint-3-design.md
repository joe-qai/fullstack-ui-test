# Sprint 3：任务调度重构 + UI 统一 + 在线调试优化设计方案

**日期**: 2026-05-23
**版本**: v1.0
**状态**: 已完成

## 一、需求概述

本次 Sprint 3 涵盖以下需求：

| 序号 | 需求描述 | 优先级 | 模块 |
|------|----------|--------|------|
| 1 | ScriptExecutor 重构为 start/wait 模式，支持行级输出和取消 | 高 | 后端 |
| 2 | TaskDispatcher 进程即时追踪，cancel_task 硬终止子进程 | 高 | 后端 |
| 3 | 任务 ID 从随机 hex 改为顺序编号 (task_1, task_2...) | 中 | 后端 |
| 4 | 所有列表页操作按钮图标化（无文字，纯图标 + tooltip） | 中 | 前端 |
| 5 | 所有日期列统一显示为 yyyy-MM-dd HH:mm:ss 格式 | 中 | 前端 |
| 6 | 任务管理：失败原因分支展示、重新执行、中止功能 | 高 | 前端 |
| 7 | Debug.vue 工具栏精简 + iframe 双状态 + 云 URL | 高 | 前端 |
| 8 | uiautodev 双启动策略 + 全杀停止 + 平台参数 | 高 | 后端 |
| 9 | TestTaskResponse 新增 content_name 字段 | 中 | 后端 |

## 二、详细设计

### 2.1 脚本执行器重构

**现状问题**：
- `run_script()` 使用 `process.communicate()` 阻塞等待，无法实时捕获输出
- 取消任务时子进程无法被终止

**设计方案**：

```
start(script, device, project)
  ├── Popen(executable, stdout=PIPE, stderr=PIPE, text=True)
  ├── select + 逐行读取 stdout/stderr
  ├── 每行推入 self.logs
  └── 返回（后台持续读取）

wait(cancel_check=None)
  ├── 持续读取直到 EOF
  ├── 每行检查 cancel_check() 信号
  ├── 收到信号 → process.terminate() → wait(5s) → process.kill()
  ├── 收集 stdout/stderr/exit_code
  ├── 组装 result dict (status/logs/start_time/end_time/duration_ms)
  └── 返回 result
```

**关键代码**：
```python
def start(self, script, device, project=None):
    self.process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, env=env, cwd=workdir,
    )
    self._reader_thread = threading.Thread(target=self._read_output, daemon=True)
    self._reader_thread.start()

def wait(self, cancel_check=None):
    self._reader_thread.join()
    if cancel_check and cancel_check():
        self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
    stdout, stderr = self.process.communicate()
    return self._build_result(stdout, stderr)
```

**取消接口**：
- 回调函数 `cancel_check()` 在每行输出后执行
- `task_dispatcher.py` 传入 `lambda: task_id in self.cancelled_tasks`

### 2.2 任务调度器增强

**进程追踪**：
```
_execute_on_device:
  executor = ScriptExecutor()
  result = executor.start(script, device, project)
  self.active_processes[result_id] = {
      "process": executor.process,
      "executor": executor,
      "start_time": time.time(),
  }
  result = executor.wait(cancel_check)
```

**取消逻辑**：
```python
def cancel_task(self, task_id):
    if task_id in self.active_processes:
        entry = self.active_processes[task_id]
        self.cancelled_tasks.add(task_id)
        entry["process"].terminate()
        try:
            entry["process"].wait(timeout=5)
        except subprocess.TimeoutExpired:
            entry["process"].kill()
```

### 2.3 顺序 ID 生成器

```python
def next_id(prefix: str, model_class, db: Session) -> str:
    last = db.query(model_class).order_by(model_class.id.desc()).first()
    if last and last.id.startswith(prefix):
        m = re.search(rf'{re.escape(prefix)}(\d+)$', last.id)
        if m:
            return f"{prefix}{int(m.group(1)) + 1}"
    return f"{prefix}1"
```

- 生成格式：`task_1`, `task_2`, ... `report_1` ...
- 在 `create_task` 中调用，覆盖默认随机 ID

### 2.4 前端 UI 统一

#### 2.4.1 日期格式化

**工具函数** (`frontend/src/utils/format.js`)：
```javascript
export function formatDate(isoString) {
  if (!isoString) return ''
  const d = new Date(isoString)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}
```

**变更方式**：列定义从 `dataIndex: 'created_at'` 改为 `key: 'createdAt', slots: { customRender: 'createdAt' }`，模板内 `<template #createdAt>...</template>` 调用 `formatDate`

**涉及视图**：Projects, Reports, ScriptManagement, Tasks, ProjectDetail, APKManagement（uploadedAt）

#### 2.4.2 按钮图标化

**设计原则**：
- 所有列表页操作列按钮去掉文字标签
- 使用 `a-tooltip` 包裹纯图标按钮
- 每个操作使用对应的 Ant Design Vue 图标

**图标映射**：

| 操作 | 图标 | 颜色 |
|------|------|------|
| 查看/预览 | EyeOutlined | default |
| 编辑 | EditOutlined | default |
| 删除 | DeleteOutlined | danger |
| 下载 | DownloadOutlined | default |
| 重新执行 | RedoOutlined | default |
| 中止 | CloseCircleOutlined | danger |
| 断开 | DisconnectOutlined | danger |
| 重连 | ReloadOutlined | default |
| 连接 | LinkOutlined | default |
| 离线 | MinusCircleOutlined | disabled |
| 跨项目复制 | CopyOutlined | default |
| 启用/禁用 | CheckCircleOutlined/StopOutlined | default |

### 2.5 任务管理增强

**失败原因展示流程**：
```javascript
getFailureReason(record):
  if completed → ''
  if running    → ''
  if cancelled  → '已取消'
  if failed:
    1. 优先返回 record.error_message
    2. 查找 results 中第一个 failed 的 error_message
    3. 查找 steps 中第一个 failed 的 error_message
    4. 兜底 '执行失败'
```

**颜色映射**：
```javascript
getFailureColor(status):
  completed → '#52c41a'  (绿)
  failed    → '#ff4d4f'  (红)
  cancelled → '#faad14'  (黄)
  default   → 'inherit'
```

**操作按钮**：
- 状态为 `failed`/`cancelled`：显示重新执行按钮（RedoOutlined），调用 `executeTaskApi`
- 状态为 `running`：显示中止按钮（CloseCircleOutlined），调用 `abortTaskApi`
- 可删除状态：显示删除按钮（DeleteOutlined）
- 重新执行中 `executingTaskId` 防止重复点击

### 2.6 在线调试优化

#### 2.6.1 工具栏精简

**修改前**：启动/停止/重启 | 设备选择(@change) | 加载设备 | 加载主页 | 新窗口打开 | 刷新 | 全屏
**修改后**：启动/停止/重启 | 设备选择(无@change) | 加载设备 | 新窗口打开 | 全屏

- 移除 `@change="handleDeviceChange"`：设备选择不再自动加载
- 移除"加载主页"按钮
- 移除"刷新"按钮
- 设备 option 内添加平台标签 `<a-tag color="orange">{{ device.platform || 'android' }}</a-tag>`

#### 2.6.2 iframe 双状态

```
服务未运行 ──→ [a-empty] 占位提示："请先启动 uiauto.dev 服务"
服务运行中 ──→ [a-spin loading] → [iframe]
```

**URL 策略**：
```javascript
currentIframeSrc:
  if !serviceStatus.running → ''
  if currentUrl:
    currentUrl.replace('/uiautodev/', 'https://uiauto2.devsleep.com/')
  else:
    'https://uiauto2.devsleep.com/'
```

- 完全绕过 Vite proxy，直接使用云端 URL
- 启动/停止/重启均 `iframeKey++` 触发刷新

### 2.7 uiautodev 服务管理

**双启动策略**：
```python
def start(self):
    # 尝试 uiauto.dev 可执行文件
    result = subprocess.run([self.exe_path, "server", "--no-browser", "--port", str(self.port)],
                           capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        return {"success": True}
    # 回退 python -m uiautodev
    result = subprocess.run([sys.executable, "-m", "uiautodev", "server", "--no-browser", "--port", str(self.port)],
                           capture_output=True, text=True, timeout=10)
    return {"success": result.returncode == 0}
```

**停止策略**：
```python
def stop(self):
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/F", "/IM", "uiauto*"],
                       capture_output=True)
    else:
        subprocess.run(["pkill", "-f", "uiauto"],
                       capture_output=True)
```

**状态返回**：
```python
def get_status(self):
    return {
        "running": self._is_running(),
        "url": "https://uiauto2.devsleep.com",
        "host": "127.0.0.1",
        "port": 20243,
    }
```

**设备 URL 支持平台**：
```python
def get_device_url(self, serial, platform="android"):
    return f"https://uiauto2.devsleep.com/{platform}/{serial}"
```

## 三、受影响文件清单

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| backend/executors/script_executor.py | 重构 | start/wait 拆分 |
| backend/core/task_dispatcher.py | 增强 | 进程追踪 + 取消 |
| backend/core/id_generator.py | 新增 | 顺序 ID |
| backend/api/tasks.py | 修改 | 引用 id_generator |
| backend/schemas/test_task.py | 修改 | 新增 content_name |
| backend/core/uiautodev_manager.py | 重构 | 双启动 + 全杀 |
| backend/tests/test_uiautodev_manager.py | 修改 | 适配云 URL |
| frontend/src/api/index.js | 修改 | 新增 abortTask |
| frontend/src/utils/format.js | 新增 | formatDate 工具 |
| frontend/src/views/Projects.vue | 修改 | 图标 + formatDate |
| frontend/src/views/Reports.vue | 修改 | 同上 |
| frontend/src/views/ScriptManagement.vue | 修改 | 同上 |
| frontend/src/views/Tasks.vue | 修改 | 同上 + 增强 |
| frontend/src/views/Devices.vue | 修改 | 图标化 |
| frontend/src/views/Keywords.vue | 修改 | 图标化 |
| frontend/src/views/POManagement.vue | 修改 | 图标化 |
| frontend/src/views/APKManagement.vue | 修改 | 图标 + formatDate |
| frontend/src/views/TestCaseManagement.vue | 修改 | 图标化 |
| frontend/src/views/ProjectDetail.vue | 修改 | formatDate |
| frontend/src/views/Debug.vue | 重构 | 工具栏 + iframe + 云 URL |

## 四、验收标准

| 功能 | 验收标准 |
|------|----------|
| 脚本执行 | start/wait 分离，行级输出实时 push logs |
| 任务取消 | running 任务点击中止后子进程被 kill，状态变为 cancelled |
| 顺序 ID | 新建任务 ID 为 task_1, task_2... 非随机 hex |
| 按钮图标化 | 9 个视图操作列无文字按钮，hover 有 tooltip |
| 日期格式 | 所有日期列显示 yyyy-MM-dd HH:mm:ss |
| 任务失败原因 | cancelled 显示"已取消"，failed 递归查找错误信息 |
| 重新执行 | failed/cancelled 任务可点击重新执行 |
| 调试页面 | 服务未运行显示占位，运行后 iframe 加载云 URL |
| uiautodev 启动 | uiauto.dev 失败自动回退 python -m |
| uiautodev 停止 | 所有 uiauto 相关进程被终止 |

## 五、风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| 子进程杀不干净 | 端口占用无法重启 | taskkill /F /IM uiauto* 全杀 |
| iframe 跨域 | 调试页面空白 | 使用云 URL 绕过代理跨域 |
| 编码问题 | Python/PowerShell 中文乱码 | 使用 .py 脚本执行编辑 |
| vite.config.js 被 checkout 恢复 | 代理配置丢失 | 确认 proxy target 为 uiauto2.devsleep.com |
