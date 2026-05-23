# Sprint 3：任务调度重构 + UI 统一 + 在线调试优化实施计划

**日期**: 2026-05-23
**版本**: v1.0
**关联设计**: specs/2026-05-23-sprint-3-design.md

## 一、计划概述

本计划基于 Sprint 3 设计文档，详细描述任务调度重构、前端 UI 统一和在线调试优化三大模块的实施步骤、文件变更和时间预估。总变更文件数：22 个（20 修改 + 2 新增）。

## 二、任务分解

### Task 1：脚本执行器重构（3 文件）

| 子任务 | 描述 | 文件 | 预估时间 |
|--------|------|------|----------|
| 1.1 | ScriptExecutor 拆分为 start()/wait()，行级输出 | executors/script_executor.py | 60分钟 |
| 1.2 | run_script() 降级为 start() + wait() 代理 | 同上 | 15分钟 |
| 1.3 | run() 统一入口（Query Script → start → wait） | 同上 | 20分钟 |
| 1.4 | cancel_check 回调函数支持 | 同上 | 15分钟 |
| 1.5 | TaskDispatcher 进程即时追踪 | core/task_dispatcher.py | 20分钟 |
| 1.6 | cancel_task 硬终止（terminate → wait → kill） | 同上 | 15分钟 |
| 1.7 | tasks.py 引用 id_generator 顺序 ID | api/tasks.py | 10分钟 |
| 1.8 | 测试验证 | pytest tests/ | 15分钟 |

### Task 2：前端 UI 统一（13 文件）

| 子任务 | 描述 | 文件 | 预估时间 |
|--------|------|------|----------|
| 2.1 | 创建 formatDate 工具 | utils/format.js (新) | 10分钟 |
| 2.2 | 创建 id_generator | core/id_generator.py (新) | 10分钟 |
| 2.3 | Projects.vue 图标化 + formatDate | Projects.vue | 20分钟 |
| 2.4 | Reports.vue 图标化 + formatDate | Reports.vue | 20分钟 |
| 2.5 | ScriptManagement.vue 图标化 + formatDate | ScriptManagement.vue | 20分钟 |
| 2.6 | Tasks.vue 图标化 + formatDate + 增强 | Tasks.vue | 30分钟 |
| 2.7 | Devices.vue 图标化 | Devices.vue | 15分钟 |
| 2.8 | Keywords.vue 图标化 | Keywords.vue | 10分钟 |
| 2.9 | POManagement.vue 图标化 | POManagement.vue | 15分钟 |
| 2.10 | APKManagement.vue 图标化 + formatDate | APKManagement.vue | 15分钟 |
| 2.11 | TestCaseManagement.vue 图标化 | TestCaseManagement.vue | 10分钟 |
| 2.12 | ProjectDetail.vue formatDate | ProjectDetail.vue | 5分钟 |
| 2.13 | api/index.js 新增 abortTask | api/index.js | 5分钟 |
| 2.14 | schema content_name | schemas/test_task.py | 5分钟 |
| 2.15 | 前端构建验证 | npm run build | 10分钟 |

### Task 3：在线调试优化（3 文件）

| 子任务 | 描述 | 文件 | 预估时间 |
|--------|------|------|----------|
| 3.1 | uiautodev_manager 双启动策略 | uiautodev_manager.py | 25分钟 |
| 3.2 | 停止全杀（taskkill/pkill） | 同上 | 15分钟 |
| 3.3 | get_status 返回云 URL、平台参数 | 同上 | 10分钟 |
| 3.4 | 测试适配云 URL + platform | test_uiautodev_manager.py | 10分钟 |
| 3.5 | Debug.vue 工具栏精简 | Debug.vue | 20分钟 |
| 3.6 | iframe 双状态 + 云 URL + 服务感知 | 同上 | 30分钟 |
| 3.7 | loadDevice 使用 device.platform | 同上 | 10分钟 |
| 3.8 | 验证调试页面加载 | 手动测试 | 10分钟 |

## 三、任务流程图

```
┌───────────────────────────────────────────────────────────────┐
│                           开始                                 │
└───────────────────────────────┬───────────────────────────────┘
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
              ┌──────────┐ ┌──────┐ ┌──────────────┐
              │  Task 1  │ │Task 2│ │   Task 3     │
              │ 后端重构 │ │前端UI│ │ 在线调试优化  │
              └─────┬────┘ └──┬───┘ └──────┬───────┘
                    │         │             │
          ┌─────────┤         │             │
          ▼         ▼         │             │
    ┌────────┐ ┌────────┐     │             │
    │1.1-1.3 │ │1.4-1.6 │     │             │
    │Executor│ │Dispatcher│    │             │
    └────┬───┘ └────┬────┘     │             │
         │          │          │             │
         └──────────┼──────────┼─────────────┘
                    ▼          ▼             ▼
              ┌─────────────────────────────────┐
              │     Task 4：测试验证 & 提交     │
              │ pytest + npm run build + push   │
              └─────────────────────────────────┘
```

## 四、资源需求

| 资源类型 | 需求 |
|----------|------|
| 开发环境 | Python 3.10+, Node.js 18+, npm |
| 前端工具 | Vue 3, Ant Design Vue, Vite |
| 后端工具 | FastAPI, SQLAlchemy, SQLite |
| 测试工具 | pytest, Vue Router |
| 云端服务 | uiauto2.devsleep.com 可访问（调试页面试用） |

## 五、时间预估汇总

| 任务 | 子任务数 | 预估时间 |
|------|----------|----------|
| Task 1：后端重构 | 8 | 170分钟 |
| Task 2：前端 UI 统一 | 15 | 200分钟 |
| Task 3：在线调试优化 | 8 | 130分钟 |
| **总计** | **31** | **500分钟 ≈ 8.3小时** |

## 六、验收测试用例

### 后端测试
1. `pytest backend/tests/test_uiautodev_manager.py -v` — 全绿通过
2. 创建任务检查 ID 格式（task_1, task_2 ...）
3. 执行 running 任务，调用 abort API → 状态变为 cancelled
4. 启动 uiautodev 服务 → 服务状态显示 green 运行中

### 前端构建测试
1. `cd frontend && npm run build` — 构建通过，无错误
2. 所有列表页操作列无文字按钮 → 只有图标
3. Hover 图标显示对应的中文 tooltip
4. 时间列格式为 `2026-05-23 14:30:00` 格式
5. 服务未运行时，调试页面 iframe 区域显示占位提示

### 功能测试
1. 失败任务显示正确错误原因（cancelled → 已取消）
2. 重新执行按钮只在 failed/cancelled 状态可见
3. 中止按钮只在 running 状态可见
4. 设备选择器显示 platform 标签（android/iOS/HarmonyOS）

## 七、风险控制

| 风险 | 应对措施 |
|------|----------|
| Debug.vue 编码损坏 | 用 Python 脚本直接写文件，避免 PowerShell 转义 |
| vite.config.js 代理丢失 | 确认 proxy target 为 uiauto2.devsleep.com |
| python -m uiautodev 不可用 | 双启动策略，自动回退 |
| 子进程残留 | taskkill /F /IM uiauto* 全杀 |
| 前端构建失败（图标未注册） | 检查每个 View 的 import 是否完整 |
