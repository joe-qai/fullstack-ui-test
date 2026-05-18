# UI AutoTest Platform

> 多端 UI 自动化测试平台 —— 以 Android 为试点，支持关键字驱动和脚本执行模式。

[![Python](https://img.shields.io/badge/Python-3.14-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green)](https://fastapi.tiangolo.com)
[![Vue](https://img.shields.io/badge/Vue-3.0-4FC08D)](https://vuejs.org)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57)](https://sqlite.org)

## 功能特性

### 核心功能

- **项目管理**: 创建、管理测试项目，支持多平台（Android/iOS/Web/鸿蒙）
- **页面对象（PO）管理**: 可视化定义页面和元素，支持 resource-id、xpath、text、class 等多种定位方式
- **关键字驱动**: 内置 10+ 关键字（click、input、swipe、wait、assert 等），支持自定义关键字
- **脚本导入**: 支持导入现有 Python 测试脚本（.py），自动解析类名和方法名
- **测试用例编排**: 通过拖拽方式编排关键字步骤，创建测试用例
- **设备管理**: 自动扫描 ADB 设备，支持 USB 和 WiFi 连接
- **任务调度**: 多设备并发执行测试任务，支持关键字型和脚本型用例混合执行
- **实时日志**: WebSocket 推送执行日志，实时查看测试进度
- **设备调试**: 集成 uiautodev，支持 Android/iOS/鸿蒙元素定位和实时查看

### 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                    Vue 3 前端 (SPA)                       │
│         Dashboard | Projects | Devices | Tasks | Debug    │
└─────────────────────┬───────────────────────────────────┘
                      │ REST API + WebSocket
┌─────────────────────┴───────────────────────────────────┐
│              FastAPI 后端 (单体进程)                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ Projects │ │   POs    │ │ Keywords │ │  Tasks   │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ Devices  │ │ Scripts  │ │ Reports  │ │  Debug   │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
│  ┌──────────────────────────────────────────────────┐  │
│  │  AndroidExecutor  |  ScriptExecutor  |  (Future)   │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────┐                                       │
│  │   SQLite DB   │                                       │
│  └──────────────┘                                       │
└─────────────────────────────────────────────────────────┘
```

## 快速开始

### 环境要求

- Python 3.14+
- Node.js 18+
- ADB (Android Debug Bridge)

### 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd MultiUiAutoTest

# 安装 Python 依赖
pip install -r backend/requirements.txt

# 安装前端依赖
cd frontend
npm install
```

### 启动服务

```bash
# 启动后端（端口 8000）
cd backend
python main.py

# 启动前端（端口 5173，开发模式）
cd frontend
npm run dev
```

### 访问应用

- **前端界面**: http://localhost:5173
- **API 文档**: http://localhost:8000/docs
- **后端健康检查**: http://localhost:8000/health

## 项目结构

```
MultiUiAutoTest/
├── backend/                     # Python 后端
│   ├── main.py                  # FastAPI 入口
│   ├── config.py                # 配置管理
│   ├── db/                      # 数据库
│   │   ├── database.py          # SQLAlchemy 连接
│   │   └── init_db.py           # 初始化 + 关键字种子
│   ├── models/                  # SQLAlchemy 数据模型
│   │   ├── project.py
│   │   ├── page_object.py
│   │   ├── element.py
│   │   ├── keyword.py
│   │   ├── test_case.py
│   │   ├── case_step.py
│   │   ├── script.py
│   │   ├── device.py
│   │   ├── test_task.py
│   │   └── task_result.py
│   ├── schemas/                 # Pydantic 数据验证
│   ├── api/                     # FastAPI 路由
│   │   ├── projects.py
│   │   ├── pages.py
│   │   ├── keywords.py
│   │   ├── cases.py
│   │   ├── scripts.py
│   │   ├── devices.py
│   │   ├── tasks.py
│   │   └── debug.py
│   ├── core/                    # 核心引擎
│   │   ├── keyword_engine.py
│   │   ├── po_manager.py
│   │   ├── device_scanner.py
│   │   ├── task_dispatcher.py
│   │   └── uiautodev_manager.py
│   ├── executors/               # 执行引擎
│   │   ├── base_executor.py
│   │   ├── android_executor.py  # uiautomator2
│   │   └── script_executor.py   # subprocess
│   ├── websocket/               # WebSocket 日志
│   │   └── log_stream.py
│   └── tests/                   # 测试
│       ├── test_db.py
│       ├── test_keyword_engine.py
│       ├── test_po_manager.py
│       ├── test_device_scanner.py
│       ├── test_projects.py
│       ├── test_executors.py
│       ├── test_task_dispatcher.py
│       ├── test_uiautodev_manager.py
│       └── test_integration.py
├── frontend/                    # Vue 3 前端
│   ├── src/
│   │   ├── api/                 # Axios API 客户端
│   │   ├── views/               # 页面组件
│   │   │   ├── Dashboard.vue
│   │   │   ├── Projects.vue
│   │   │   ├── ProjectDetail.vue
│   │   │   ├── Devices.vue
│   │   │   ├── Tasks.vue
│   │   │   ├── Keywords.vue
│   │   │   └── Debug.vue
│   │   ├── router/              # Vue Router
│   │   └── App.vue              # 布局组件
│   └── package.json
├── scripts/                     # 上传的 .py 脚本存储
├── reports/                     # 测试报告存储
└── data/                        # SQLite 数据库
```

## API 文档

### 核心端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/api/projects` | GET/POST | 项目列表 / 创建 |
| `/api/projects/{id}` | GET/PUT/DELETE | 项目详情 / 更新 / 删除 |
| `/api/projects/{id}/pages` | GET/POST | 页面对象列表 / 创建 |
| `/api/projects/{id}/pages/{pid}/elements` | GET/POST | 元素列表 / 创建 |
| `/api/keywords` | GET | 关键字列表 |
| `/api/projects/{id}/cases` | GET/POST | 测试用例列表 / 创建 |
| `/api/projects/{id}/scripts` | GET/POST | 脚本列表 / 上传 |
| `/api/devices` | GET | 设备列表 |
| `/api/devices/scan` | POST | 扫描设备 |
| `/api/tasks` | GET/POST | 任务列表 / 创建 |
| `/api/tasks/{id}/execute` | POST | 执行任务 |
| `/api/debug/uiautodev/status` | GET | uiautodev 状态 |

完整 API 文档启动后端后访问: http://localhost:8000/docs

## 测试

```bash
# 运行所有测试
cd backend
pytest tests/ -v

# 运行特定测试
pytest tests/test_integration.py -v

# 运行并生成覆盖率报告
pytest tests/ --cov=backend --cov-report=html
```

### 测试覆盖

| 测试文件 | 测试数 | 说明 |
|----------|--------|------|
| `test_db.py` | 1 | 数据库连接 |
| `test_keyword_engine.py` | 4 | 关键字引擎 |
| `test_po_manager.py` | 3 | PO 管理器 |
| `test_device_scanner.py` | 2 | 设备扫描器 |
| `test_projects.py` | 5 | 项目 API |
| `test_executors.py` | 8 | 执行器 |
| `test_task_dispatcher.py` | 3 | 任务调度器 |
| `test_uiautodev_manager.py` | 3 | uiautodev 管理器 |
| `test_integration.py` | 12 | 集成测试 |
| **总计** | **41** | **全部通过** |

## 开发计划

### 已完成

- [x] Phase 1: 后端基础架构（FastAPI + SQLite + CRUD）
- [x] Phase 2: 执行引擎层（AndroidExecutor + ScriptExecutor + TaskDispatcher）
- [x] Phase 3: Vue 3 前端界面（Ant Design Vue）
- [x] Phase 4: uiautodev 集成（设备调试）
- [x] 测试覆盖（41 个测试，全部通过）

### 未来扩展

- [ ] Web 测试引擎（Playwright）
- [ ] iOS 测试引擎（XCUITest）
- [ ] 鸿蒙测试引擎（ArkUI）
- [ ] 报告生成（HTML/PDF）
- [ ] CI/CD 集成
- [ ] 分布式执行

## 技术选型

| 层面 | 选型 | 理由 |
|------|------|------|
| 后端 | Python + FastAPI | 高性能异步框架，原生 WebSocket 支持 |
| 前端 | Vue 3 + Ant Design Vue | 生态丰富，组件完善 |
| 数据库 | SQLite | 轻量级，无需安装数据库服务 |
| Android 引擎 | uiautomator2 | Python 原生，支持 USB/WiFi |
| 设备调试 | uiautodev | 支持 Android/iOS/鸿蒙 |
| 测试 | pytest | Python 标准测试框架 |

## 贡献指南

1. Fork 项目
2. 创建分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

[MIT](LICENSE)

## 致谢

- [FastAPI](https://fastapi.tiangolo.com)
- [Vue.js](https://vuejs.org)
- [uiautomator2](https://github.com/openatx/uiautomator2)
- [uiautodev](https://uiauto.dev)
- [Ant Design Vue](https://antdv.com)
