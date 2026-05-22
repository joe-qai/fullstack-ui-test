# AGENTS.md — MultiUiAutoTest

> 多端 UI 自动化测试平台（Android 试点），FastAPI + Vue 3 + SQLite。

## 快速命令

```bash
# 启动后端（端口 9000）
cd backend && python main.py

# 启动前端开发服务器（端口 5174，Vite 代理到后端）
cd frontend && npm run dev

# 一键启动（Windows）
start.bat

# 运行所有后端测试
cd backend && pytest tests/ -v

# 运行单个测试文件
cd backend && pytest tests/test_integration.py -v
```

## 架构要点

- **后端**: FastAPI 单体进程，`backend/main.py` 入口，端口 **9000**（不是 8000）
- **前端**: Vue 3 + Ant Design Vue + Vite，开发端口 **5174**（不是 5173）
- **数据库**: SQLite，路径 `data/autotest.db`（相对项目根目录）
- **配置**: `backend/config.py` 定义所有路径和端口常量
- **测试 DB**: `conftest.py` 使用独立 `data/test.db`，需手动种子化关键字数据

## 关键目录约定

| 目录 | 用途 |
|------|------|
| `backend/api/` | FastAPI 路由模块，通过 `api/__init__.py` 聚合为 `api_router` |
| `backend/models/` | SQLAlchemy ORM 模型 |
| `backend/schemas/` | Pydantic 数据验证模型 |
| `backend/core/` | 核心业务逻辑（引擎、扫描器、调度器） |
| `backend/executors/` | 测试执行器（Android/Script） |
| `backend/tests/` | pytest 测试，`conftest.py` 提供 `client` fixture |
| `scripts/` | 用户上传的 .py 测试脚本存储 |
| `reports/` | 测试报告存储 |
| `data/` | SQLite 数据库 + APK 文件 |

## 重要注意事项

1. **端口**: 后端 9000，前端 5174。README 写的 8000/5173 已过时。
2. **Vite 代理**: `frontend/vite.config.js` 配置了 `/api`、`/health`、`/docs`、`/ws` 代理到后端。
3. **CORS**: `config.py` 中 `cors_origins` 包含 `http://localhost:5173` 和 `5174` 开发端口。
4. **路径引用**: `backend/config.py` 使用 `Path(__file__).parent.parent` 指向项目根目录。
5. **测试隔离**: 测试使用独立 DB，`conftest.py` 的 `setup_test_db` fixture 会种子化内置关键字。
6. **SPA 回退**: `main.py` 包含 SPA fallback 路由，构建后的前端可由后端直接服务。

## 测试须知

- 测试从 `backend/` 目录运行（`sys.path` 插入逻辑在 `conftest.py`）
- `client` fixture 提供 `TestClient(app)` 实例
- `setup_test_db` 是 session 级 fixture，自动创建表并种子化关键字
- 集成测试可能依赖 ADB 设备状态，注意 mock

## 前端构建

```bash
# 构建产物输出到 frontend/dist/
cd frontend && npm run build

# 构建后后端可服务静态文件（main.py 检查 frontend/dist 是否存在）
```

## 已知问题（docs/issues.md）

- 前端样式问题（Ant Design Vue 样式导入）
- 部分 API 缺少 CORS 预检处理
- 缺少输入验证中间件和认证授权
