# UiTesting Platform

> 智能驱动的多端 UI 自动化测试平台，基于关键字驱动和 PO 设计模式

[![Python](https://img.shields.io/badge/Python-3.14-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green)](https://fastapi.tiangolo.com)
[![Vue](https://img.shields.io/badge/Vue-3.0-4FC08D)](https://vuejs.org)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57)](https://sqlite.org)

## 平台简介

UiTesting 是一款面向 QA 团队的智能化 UI 自动化测试平台，采用**关键字驱动** + **PO（Page Object）设计模式**，支持 Android 等多平台自动化测试。

### 核心特性

- **关键字驱动**: 内置基础、平台、断言类关键字，低代码编写测试用例
- **PO 设计模式**: 页面对象统一管理元素，提高复用率和可维护性
- **多端支持**: Android（uiautomator2）、支持扩展 iOS/鸿蒙
- **实时调试**: 集成 uiautodev，浏览器内直接调试真机
- **任务调度**: 多设备并发执行，失败重试，结果分析
- **完整报告**: 截图、日志、失败原因追踪

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 后端 | Python 3.14 + FastAPI | 高性能异步框架，原生 WebSocket |
| 前端 | Vue 3 + Ant Design Vue | 响应式管理后台 |
| 数据库 | SQLite | 轻量级，无需独立部署 |
| Android | uiautomator2 | 跨平台 UI 自动化 |
| 设备调试 | uiautodev | 浏览器内实时调试真机 |

## 快速开始

### 环境要求

- Python 3.14+
- Node.js 18+
- ADB (Android Debug Bridge)

### 启动服务

```bash
# 克隆项目
git clone https://github.com/joe-qai/fullstack-ui-test.git
cd fullstack-ui-test

# 启动后端（端口 9000）
cd backend
pip install -r requirements.txt
python main.py

# 新开终端 - 启动前端（端口 5174）
cd frontend
npm install
npm run dev
```

### 访问平台

- 前端界面: http://localhost:5174
- API 文档: http://localhost:9000/docs

## 功能模块

### 对象管理
统一管理页面和元素，支持 text、resourceId、xpath、className 等定位方式

### 关键字管理
内置三类关键字：基础操作、平台能力、断言验证，支持自定义扩展

### 用例管理
拖拽编排关键字步骤，创建可复用的测试用例

### 任务管理
创建测试任务，选择执行设备，查看任务状态和结果

### 报告管理
查看测试报告，包含执行截图、日志和失败原因

### 在线调试
浏览器内实时调试真机设备，查看屏幕截图和元素信息

## 项目结构

```
fullstack-ui-test/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── config.py           # 配置管理
│   ├── api/                # REST API 路由
│   ├── models/             # SQLAlchemy 模型
│   ├── schemas/            # Pydantic 验证
│   ├── core/               # 核心引擎
│   │   ├── keyword_engine.py
│   │   ├── po_manager.py
│   │   ├── device_scanner.py
│   │   ├── task_dispatcher.py
│   │   └── uiautodev_manager.py
│   └── executors/          # 测试执行器
│       ├── android_executor.py
│       └── script_executor.py
├── frontend/
│   └── src/
│       ├── views/          # 页面组件
│       ├── api/            # API 客户端
│       ├── router/         # 路由配置
│       └── App.vue         # 布局组件
├── data/                   # 数据库和 APK 文件
├── scripts/                # 用户上传的测试脚本
└── reports/                # 测试报告
```

## API 文档

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/projects` | GET/POST | 项目管理 |
| `/api/pages` | GET/POST | 页面对象管理 |
| `/api/elements` | GET/POST | 元素管理 |
| `/api/keywords` | GET | 关键字列表 |
| `/api/cases` | GET/POST | 用例管理 |
| `/api/devices` | GET | 设备列表 |
| `/api/tasks` | GET/POST | 任务管理 |
| `/api/tasks/{id}/execute` | POST | 执行任务 |
| `/api/debug/uiautodev/status` | GET | uiautodev 状态 |

## 测试

```bash
# 运行后端测试
cd backend
pytest tests/ -v
```

## 开源地址

https://github.com/joe-qai/fullstack-ui-test

## 许可证

MIT License
