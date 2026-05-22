# AGENTS.md — UiTesting Platform

> 多端 UI 自动化测试平台，基于关键字驱动和 PO 设计模式，FastAPI + Vue 3 + SQLite。

## 快速命令

```bash
# 启动后端（端口 9000）
cd backend && python main.py

# 启动前端（端口 5174，Vite 代理到后端）
cd frontend && npm run dev

# 运行后端测试
cd backend && pytest tests/ -v
```

## 架构要点

- **后端**: FastAPI 单体进程，`backend/main.py` 入口，端口 **9000**
- **前端**: Vue 3 + Ant Design Vue + Vite，开发端口 **5174**
- **数据库**: SQLite，路径 `data/autotest.db`（相对项目根目录）
- **配置**: `backend/config.py` 定义所有路径和端口常量
- **uiautodev**: 端口 **20243**，支持浏览器内调试真机

## 关键目录

| 目录 | 用途 |
|------|------|
| `backend/api/` | FastAPI 路由模块 |
| `backend/models/` | SQLAlchemy ORM 模型 |
| `backend/schemas/` | Pydantic 数据验证模型 |
| `backend/core/` | 核心业务逻辑（引擎、调度器） |
| `backend/executors/` | 测试执行器（Android/Script） |
| `backend/tests/` | pytest 测试 |
| `frontend/src/views/` | Vue 页面组件 |
| `data/` | SQLite 数据库 + APK 文件 |
| `scripts/` | 用户上传的测试脚本 |
| `reports/` | 测试报告存储 |

## 菜单结构

- **首页**: 仪表盘
- **资源管理**: 项目管理、关键字管理
- **对象管理**: PO 页面对象和元素管理
- **执行中心**: 任务管理、报告管理
- **在线调试**: uiautodev 真机调试

## Vite 代理配置

`frontend/vite.config.js` 配置了以下代理：
- `/api` → 后端 API
- `/health` → 健康检查
- `/docs` → API 文档
- `/ws` → WebSocket
- `/uiautodev` → uiautodev 服务 (端口 20243)

## 注意事项

1. **端口**: 后端 9000，前端 5174
2. **uiautodev**: 默认端口 20243，启动命令 `uiauto.dev.exe server --no-browser --port 20243`
3. **SPA 回退**: `main.py` 包含 SPA fallback 路由

## 测试

- 测试从 `backend/` 目录运行
- `conftest.py` 的 `setup_test_db` fixture 自动创建表并种子化关键字
- 集成测试可能依赖 ADB 设备状态
