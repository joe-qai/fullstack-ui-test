# UI 自动化测试平台设计文档

> 日期：2026-05-18  
> 状态：已确认  
> 范围：Android 试点全栈

## 1. 项目概述

构建一个多端 UI 自动化测试平台，非 Agent 项目。采用**关键字驱动 + PO（Page Object）设计模式**。以 Android 端 App 自动化测试为试点，后续考虑接入 Web、iOS、鸿蒙等平台。

核心约束：
- 本地部署，不搞远程集群
- USB 直连或局域网 WiFi 连真机
- 不使用 Redis/Celery 等消息队列策略
- 轻量部署，一条命令启动

额外需求：
- 兼容已有 Python 自动化脚本：支持直接导入现存的 .py 测试脚本文件到平台管理，执行时用对应引擎运行脚本
- 项目级挂载：所有脚本和测试用例都挂载在项目下，因为不同项目的元素/文本/逻辑有差异
- 前端调试入口：集成 uiautodev（启动命令 `uiauto.dev`）作为设备元素定位工具，USB 连设备后实时查看和定位元素，支持 Android、iOS、鸿蒙

## 2. 技术选型

| 层面 | 选型 | 理由 |
|------|------|------|
| 后端语言 | Python | uiautomator2 是 Python 库，无需跨语言调用 |
| Web 框架 | FastAPI | 高性能异步框架，自带 WebSocket 支持 |
| 前端框架 | Vue 3 + Ant Design Vue | 生态大、组件丰富、后台管理系统标配 |
| 数据库 | SQLite | 轻量级，无需安装数据库服务，适合本地部署 |
| Android 测试引擎 | uiautomator2 | Python 原生，支持 USB/WiFi 连真机 |
| Web 测试引擎（未来） | Playwright | 多浏览器支持 |
| iOS 测试引擎（未来） | XCUITest | iOS 官方测试框架 |
| 鸿蒙测试引擎（未来） | HarmonyOS ArkUI | 鸿蒙官方框架 |
| 元素定位调试 | uiautodev (`uiauto.dev`) | 支持 Android/iOS/鸿蒙元素定位和实时查看 |

## 3. 整体架构

采用**单体壳 + 插件化引擎**架构：外在部署像单体一样简单（一个进程启动），内在结构插件化（每种设备类型是独立的执行引擎适配器）。

```
┌─────────────────────────────────────────────────────────┐
│                    Vue 3 前端 (SPA)                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │项目管理   │ │PO管理     │ │关键字编排 │ │测试报告   │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐               │
│  │脚本导入   │ │设备调试   │ │任务执行   │               │
│  │(.py文件) │ │uiautodev │ │并发调度   │               │
│  └──────────┘ └──────────┘ └──────────┘               │
└─────────────────────┬───────────────────────────────────┘
                      │ REST API + WebSocket
┌─────────────────────┴───────────────────────────────────┐
│              FastAPI 后端 (单体进程)                       │
│                                                          │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  API Router  │  │ TaskDispatch │  │ KeywordEngine │  │
│  │  (路由层)    │  │ (并发调度器)  │  │ (关键字引擎)  │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐ │
│  │  POManager   │  │  ReportGen   │  │ ScriptImporter │ │
│  │  (PO管理器)  │  │  (报告生成)  │  │ (脚本导入器)   │ │
│  └──────────────┘  └──────────────┘  └───────────────┘ │
│                                                          │
│  ┌─────────────────── 执行引擎层 ──────────────────────┐│
│  │                                                      ││
│  │  ┌──────────────────┐  ┌──────────────────┐        ││
│  │  │ AndroidExecutor   │  │ (未来)WebExecutor │        ││
│  │  │ (uiautomator2)    │  │ (Playwright)     │        ││
│  │  └──────────────────┘  └──────────────────┘        ││
│  │  ┌──────────────────┐  ┌──────────────────┐        ││
│  │  │ (未来)iOSExecutor │  │ (未来)HarmExecutor│        ││
│  │  │ (XCUITest)        │  │ (ArkUI)          │        ││
│  │  └──────────────────┘  └──────────────────┘        ││
│  └──────────────────────────────────────────────────────┘│
│                                                          │
│  ┌──────────────┐                                        │
│  │   SQLite DB   │                                        │
│  └──────────────┘                                        │
└─────────────────────────────────────────────────────────┘
                      │
          ┌───────────┴───────────┐
          │    本地真机集群        │
          │  USB/WiFi 连接设备    │
          │  Device-1  Device-2   │
          │  Device-3  Device-N   │
          └───────────────────────┘
```

**设计思想**：

1. **单体壳**：一个 Python 进程启动整个服务（`python main.py` 一键启动）
2. **插件化引擎层**：执行引擎通过抽象基类 `BaseExecutor` 定义接口，Android 实现具体逻辑。未来新增端只需实现 `BaseExecutor` 子类
3. **并发调度器**：`TaskDispatcher` 使用 `ThreadPoolExecutor`，每个设备分配一个线程，支持同类型多台和不同类型混合并发执行
4. **实时反馈**：FastAPI WebSocket 推送执行状态、日志到前端

## 4. 核心模块设计

### 4.1 关键字引擎（KeywordEngine）

关键字是测试步骤的基础操作单元，分三层定义：

| 层级 | 类型 | 示例 | 说明 |
|------|------|------|------|
| L1 | 基础操作关键字 | `click`、`input`、`swipe`、`wait_element` | 所有平台通用，对应 UI 最基本操作 |
| L2 | 平台特有关键字 | `press_back`(Android)、`scroll_to`(Android) | 特定平台的操作，如 Android 的返回键 |
| L3 | 自定义关键字 | `login_with_credential`、`submit_order` | 用户通过 PO 组合封装的业务关键字 |

**关键字编排方式**（前端可视化）：

用户创建一个"测试用例"，由多个"步骤"组成：
- 每个步骤 = 一个关键字 + 一个 PO 元素 + 参数
- 例如：步骤1 = `click`(关键字) + `LoginPage.btn_login`(PO元素) + 无参数
- 例如：步骤2 = `input`(关键字) + `LoginPage.input_username`(PO元素) + `"testuser"`(参数)

**关键字数据模型**：
```json
{
  "keyword": {
    "id": "kw_001",
    "name": "click",
    "category": "basic",
    "platform": "all",
    "params": [],
    "description": "点击指定元素"
  },
  "test_case": {
    "id": "tc_001",
    "name": "登录测试",
    "steps": [
      {
        "order": 1,
        "keyword_id": "kw_001",
        "po_element_id": "pe_001",
        "params": {}
      },
      {
        "order": 2,
        "keyword_id": "kw_002",
        "po_element_id": "pe_002",
        "params": {"text": "testuser"}
      }
    ]
  }
}
```

### 4.2 PO 管理器（POManager）

前端可视化定义 PO：

- 用户创建一个"页面"（如 LoginPage）
- 在页面中添加多个"元素"，每个元素包含：
  - 名称：`btn_login`
  - 定位方式：`resource-id` / `xpath` / `text` / `class`
  - 定位值：`com.app:id/login_button`
- PO 下可定义"操作"（如 `do_login`），由多个关键字步骤组成——即 L3 自定义关键字

**PO 数据模型**：
```json
{
  "page_object": {
    "id": "po_001",
    "name": "LoginPage",
    "platform": "android",
    "app_id": "com.example.app",
    "elements": [
      {
        "id": "pe_001",
        "name": "btn_login",
        "locator_type": "resource-id",
        "locator_value": "com.example:id/login_btn"
      },
      {
        "id": "pe_002",
        "name": "input_username",
        "locator_type": "resource-id",
        "locator_value": "com.example:id/username_input"
      }
    ]
  }
}
```

### 4.3 并发调度器（TaskDispatcher）

**核心逻辑**：

- 用户创建"测试任务"：选择一个测试用例 + 选择多台设备
- `TaskDispatcher` 为每台设备分配一个执行线程
- 每个线程调用对应的 `Executor` 执行测试
- 执行过程中通过 WebSocket 实时推送日志和状态

```python
# TaskDispatcher 核心伪代码
class TaskDispatcher:
    def dispatch(self, task: TestTask):
        futures = []
        with ThreadPoolExecutor(max_workers=len(task.devices)) as pool:
            for device in task.devices:
                executor = self.get_executor(device.platform)
                future = pool.submit(executor.run, task.test_case, device)
                futures.append((device.id, future))
        
        for device_id, future in futures:
            result = future.result()
            self.save_report(device_id, result)
```

**并发支持**：
- 同类型多台设备并发：同一测试用例在多台 Android 设备同时执行
- 不同类型混合并发：一个任务可同时在 Android 和（未来）Web 设备上执行
- 每台设备独立线程，互不影响

### 4.4 脚本导入器（ScriptImporter）

支持导入已有的 Python 自动化测试脚本，统一在平台中管理。

**导入流程**：
- 用户在项目下上传 .py 脚本文件
- 系统解析脚本，提取关键元信息（如文件名、类名、方法名列表）
- 脚本存储在项目的 `scripts/` 目录中，数据库记录其元信息
- 执行时，`ScriptExecutor`（继承 `BaseExecutor`）通过 subprocess 运行 .py 文件，捕获 stdout/stderr 作为日志

**脚本与关键字用例的关系**：
- 测试用例有两种类型：**关键字编排型**（通过可视化编排步骤）和 **脚本型**（直接导入 .py 文件）
- 创建任务时，选择用例不分类型——既可选用关键字编排用例，也可选脚本型用例
- `TaskDispatcher` 根据用例类型自动选择对应的执行引擎

**脚本数据模型**：
```json
{
  "script": {
    "id": "sc_001",
    "project_id": "proj_001",
    "name": "login_test.py",
    "file_path": "scripts/proj_001/login_test.py",
    "type": "python",
    "description": "登录模块自动化测试脚本",
    "classes": ["LoginTest"],
    "methods": ["test_login_success", "test_login_failure"],
    "uploaded_at": "2026-05-18T10:00:00"
  }
}
```

**脚本执行策略**：
- 脚本型用例执行时，`ScriptExecutor` 为每台设备创建一个独立子进程
- 子进程中注入设备连接参数（如设备 serial）作为环境变量或命令行参数
- 脚本需要遵循简单约定：通过 `os.environ` 或 `sys.argv` 接收设备信息
- stdout/stderr 实时通过 WebSocket 推送到前端

### 4.5 设备调试入口（uiautodev）

集成 uiautodev 作为前端调试工具，用于元素定位和实时设备查看。

**集成方式**：
- 后端通过 subprocess 启动 `uiauto.dev` 命令，获取其 Web 服务地址
- 前端通过 iframe 嵌入 uiautodev 的 Web 界面
- 支持三种设备平台：Android、iOS、鸿蒙

**调试页面功能**：
- USB 连接设备后，选择目标设备
- 实时查看设备屏幕截图
- 点击/悬停元素，自动获取元素定位信息（resource-id、xpath、text 等）
- 直接将定位到的元素信息添加到 PO 管理中（一键从调试→PO定义）
- 支持 Android、iOS、鸿蒙三种平台的元素定位

**前端路由**：
- `/projects/:id/debug` → 设备调试页（iframe 嵌入 uiautodev + 元素提取工具栏）

## 5. API 设计

### 5.1 核心 API 端点

**项目管理**
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/projects` | GET/POST | 项目列表 / 创建项目 |
| `/api/projects/{id}` | GET/PUT/DELETE | 项目详情 / 更新 / 删除 |

**PO 管理**
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/projects/{id}/pages` | GET/POST | 页面对象列表 / 创建页面 |
| `/api/projects/{id}/pages/{pid}` | GET/PUT/DELETE | 页面详情 / 更新 / 删除 |
| `/api/projects/{id}/pages/{pid}/elements` | GET/POST | 元素列表 / 创建元素 |
| `/api/projects/{id}/pages/{pid}/elements/{eid}` | GET/PUT/DELETE | 元素详情 / 更新 / 删除 |

**关键字管理**
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/keywords` | GET | 关键字列表（含平台筛选） |
| `/api/keywords/categories` | GET | 关键字分类列表 |
| `/api/projects/{id}/custom-keywords` | GET/POST | 自定义关键字列表 / 创建 |

**测试用例**
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/projects/{id}/cases` | GET/POST | 用例列表 / 创建用例（含关键字型和脚本型） |
| `/api/projects/{id}/cases/{cid}` | GET/PUT/DELETE | 用例详情 / 更新 / 删除 |

**脚本导入**
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/projects/{id}/scripts` | GET/POST | 脚本列表 / 上传脚本文件 |
| `/api/projects/{id}/scripts/{sid}` | GET/DELETE | 脚本详情 / 删除脚本 |
| `/api/projects/{id}/scripts/{sid}/parse` | POST | 解析脚本元信息（类名/方法名） |

**设备调试**
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/debug/uiautodev/status` | GET | uiautodev 服务状态 |
| `/api/debug/uiautodev/start` | POST | 启动 uiautodev 服务 |
| `/api/debug/element-capture` | POST | 从调试界面捕获元素定位信息并添加到 PO |

**设备管理**
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/devices` | GET | 已连接设备列表（自动检测） |
| `/api/devices/{did}/status` | GET | 设备实时状态 |

**任务执行**
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/tasks` | POST | 创建并启动测试任务 |
| `/api/tasks/{tid}` | GET | 任务详情 / 执行状态 |
| `/api/tasks/{tid}/reports` | GET | 任务执行报告 |
| `/ws/tasks/{tid}/logs` | WebSocket | 实时日志推送 |

## 6. 数据模型（SQLite）

```
projects          页面对象(page_objects)    elements
┌──────────┐     ┌───────────────┐        ┌────────────┐
│ id       │────→│ id            │───────→│ id         │
│ name     │     │ project_id    │        │ page_id    │
│ app_id   │     │ name          │        │ name       │
│ platform │     │ description   │        │ locator_type│
│ created  │     │ created       │        │ locator_value│
└──────────┘     └───────────────┘        └────────────┘

test_cases        case_steps              keywords
┌──────────┐     ┌─────────────┐        ┌──────────┐
│ id       │────→│ id          │        │ id       │
│ project_id│     │ case_id     │───────→│ name     │
│ name     │     │ keyword_id  │        │ category │
│ type     │     │ po_element_id│        │ platform │  ← type: "keyword"或"script"
│ description│    │ params      │        │ params   │
│ script_id│←─── │ step_order  │        │ description│  ← script_id: 脚本型用例关联
│ created  │     └─────────────┘        └──────────┘
└──────────┘

scripts           devices           test_tasks             task_results
┌──────────┐     ┌──────────┐     ┌──────────────┐       ┌─────────────┐
│ id       │     │ id       │     │ id           │       │ id          │
│ project_id│     │ name     │────→│ case_id      │       │ task_id     │
│ name     │     │ serial   │     │ devices(多选) │───────→│ device_id   │
│ file_path│     │ platform │     │ status       │       │ status      │
│ type     │     │ status   │     │ created      │       │ start_time  │
│ classes  │     │ adb_info │     └──────────────┘       │ end_time    │
│ methods  │     └──────────┘                             │ log_path    │
│ uploaded │                                             │ report_path │
└──────────┘                                             └─────────────┘
```

**设备自动检测**：后端启动时和定期（每30秒）执行 `adb devices` 扫描：
- 检测到新设备 → 自动注册到 `devices` 表
- 设备断开 → 更新状态为 `offline`
- 支持 USB 直连和 WiFi adb 连接

## 7. 前端页面结构

```
页面路由：
├── /login                → 登录页
├── /dashboard            → 仪表盘首页（测试概览/近期任务统计）
├── /projects             → 项目管理
│   ├── /projects/list    → 项目列表
│   └── /projects/:id     → 项目详情
│       ├── /po           → PO管理（页面→元素→操作）
│       ├── /cases        → 测试用例管理
│       │   ├── /cases/list → 用例列表（关键字型+脚本型）
│       │   ├── /cases/new  → 可视化编排用例（关键字拖拽组合）
│       │   └── /cases/:id  → 用例详情/编辑
│       ├── /scripts      → 脚本管理（上传/查看/解析 .py 文件）
│       ├── /tasks        → 任务执行
│       │   ├── /tasks/new  → 创建任务（选设备+选用例/脚本）
│       │   ├── /tasks/list → 任务列表/状态
│       │   └── /tasks/:id  → 任务详情（实时日志+报告）
│       └── /debug        → 设备调试（uiautodev iframe + 元素提取）
├── /devices              → 设备管理（设备列表/连接状态）
├── /reports              → 测试报告
└── /keywords             → 关键字管理（查看/自定义）
```

**核心交互页面**：

1. **PO 编辑页**：左侧页面树 → 中间元素列表 → 右侧元素属性编辑
2. **用例编排页**：左侧关键字面板 → 中间步骤编排区（拖拽排序）→ 右侧步骤参数配置
3. **脚本管理页**：上传 .py 文件 → 自动解析元信息 → 列表展示（关联到用例）
4. **设备调试页**：iframe 嵌入 uiautodev → 侧栏元素信息提取 → 一键添加到 PO
5. **任务执行页**：顶部选择用例+设备 → 中间实时日志面板（WebSocket）→ 底部每台设备的状态卡片
6. **报告页**：汇总统计 + 每台设备详细结果 + 截图展示

## 8. 执行引擎层

### 8.1 Android 执行引擎（AndroidExecutor）

**核心流程**：
```
AndroidExecutor.run(test_case, device)
    ├── 1. 连接设备: u2.connect(device.serial)
    ├── 2. 启动App: d.app_start(package=app_id)
    ├── 3. 遍历 test_case.steps:
    │   ├── 获取 PO 元素定位器
    │   ├── 执行关键字操作
    │   │   ├── click → d(resourceId=locator).click()
    │   │   ├── input → d(resourceId=locator).set_text(params.text)
    │   │   ├── swipe → d.swipe(params.direction)
    │   │   ├── wait → d(resourceId=locator).wait(timeout=10)
    │   │   └── press_back → d.press("back")
    │   ├── 每步截图保存
    │   └── 每步日志推送到 WebSocket
    ├── 4. 收集结果: 通过/失败 + 截图 + 日志
    └── 5. 生成报告: 保存到文件 + 写入数据库
```

**异常处理策略**：

| 异常 | 处理策略 |
|------|----------|
| 元素找不到 | 截图当前界面 + 标记步骤失败 + 继续下一步（可配置：失败即停/继续执行） |
| 设备断连 | 标记任务中断 + 记录已执行步骤 |
| App崩溃 | 自动重启App + 从断点继续（可配置） |

### 8.2 脚本执行引擎（ScriptExecutor）

用于执行导入的 .py 脚本文件，同样继承 `BaseExecutor`。

**核心流程**：
```
ScriptExecutor.run(test_case, device)
    ├── 1. 获取关联的脚本文件路径 (test_case.script_id → script.file_path)
    ├── 2. 构建执行环境:
    │   ├── 注入设备参数: 环境变量 DEVICE_SERIAL=device.serial
    │   ├── 注入App信息: 环境变量 APP_PACKAGE=project.app_id
    │   └── 设置工作目录: 项目根目录
    ├── 3. subprocess.Popen 执行脚本
    │   ├── 实时捕获 stdout/stderr
    │   ├── stdout/stderr 通过 WebSocket 推送前端
    │   └── 监控进程状态
    ├── 4. 等待脚本执行完成
    │   ├── 收集退出码: 0=成功, 非0=失败
    │   └── 收集完整日志输出
    └── 5. 生成报告: 保存日志 + 写入数据库
```

**脚本约定**：
- 脚本通过 `os.environ.get("DEVICE_SERIAL")` 获取设备序列号
- 脚本通过 `os.environ.get("APP_PACKAGE")` 获取目标 App 包名
- 脚本内部自行管理 uiautomator2 连接和操作
- 脚本退出码 0 表示全部通过，非 0 表示有失败

## 9. 报告生成

每台设备的执行报告包含：
- 执行摘要（通过/失败/跳过步数）
- 每步详细日志（关键字+元素+参数+执行结果）
- 每步截图（PNG，存在本地 `reports/` 目录）
- 设备信息（型号/系统版本/分辨率）
- HTML 格式可查看报告

多设备汇总报告：所有设备结果的聚合统计。

## 10. 未来扩展路径

当平台稳定后，扩展到其他端只需：

1. 实现 `BaseExecutor` 的子类（如 `WebExecutor`、`iOSExecutor`）
2. 在 `TaskDispatcher` 中注册新的执行引擎
3. 在关键字引擎中添加 L2 平台特有关键字
4. 前端设备管理中增加新平台设备检测逻辑

**扩展顺序建议**：Android（已完成） → Web → 鸿蒙 → iOS

## 11. 项目目录结构（规划）

```
MultiUiAutoTest/
├── backend/                     # Python 后端
│   ├── main.py                  # 入口：启动 FastAPI 服务
│   ├── config.py                # 配置管理
│   ├── models/                  # SQLAlchemy 数据模型
│   │   ├── project.py
│   │   ├── page_object.py
│   │   ├── element.py
│   │   ├── keyword.py
│   │   ├── test_case.py
│   │   ├── script.py
│   │   ├── device.py
│   │   ├── task.py
│   │   └── task_result.py
│   ├── api/                     # FastAPI 路由
│   │   ├── projects.py
│   │   ├── pages.py
│   │   ├── keywords.py
│   │   ├── cases.py
│   │   ├── scripts.py
│   │   ├── devices.py
│   │   ├── tasks.py
│   │   ├── reports.py
│   │   └── debug.py
│   ├── core/                    # 核心引擎
│   │   ├── keyword_engine.py    # 关键字引擎
│   │   ├── po_manager.py        # PO 管理器
│   │   ├── task_dispatcher.py   # 并发调度器
│   │   ├── report_generator.py  # 报告生成器
│   │   ├── script_importer.py   # 脚本导入解析器
│   │   ├── device_scanner.py    # 设备自动检测
│   │   └── uiautodev_manager.py # uiautodev 服务管理
│   ├── executors/               # 执行引擎层
│   │   ├── base_executor.py     # 抽象基类
│   │   ├── android_executor.py  # Android (uiautomator2)
│   │   ├── script_executor.py   # 脚本执行引擎 (.py 文件)
│   │   └── (future) web_executor.py
│   │   └── (future) ios_executor.py
│   │   └── (future) harmony_executor.py
│   ├── db/                      # 数据库
│   │   ├── database.py          # SQLite 连接管理
│   │   └── init_db.py           # 初始化脚本
│   └── websocket/               # WebSocket 管理
│       └── log_stream.py        # 实时日志推送
├── frontend/                    # Vue 3 前端
│   ├── src/
│   │   ├── views/               # 页面组件
│   │   ├── components/          # 通用组件
│   │   ├── stores/              # Pinia 状态管理
│   │   ├── api/                 # API 调用层
│   │   ├── router/              # 路由配置
│   │   └── utils/               # 工具函数
│   ├── package.json
│   └── vite.config.ts
├── scripts/                     # 上传的 .py 脚本存储目录（按项目组织）
│   └── proj_001/
│       └── login_test.py
├── reports/                     # 测试报告存储目录
├── docs/                        # 文档
└── index.html                   # 现有展示页（保留）