# MultiUiAutoTest 平台问题修复设计文档

日期: 2026-05-19
状态: 已批准

## 概述

针对平台13个已知问题，采用逐项修复策略，不做整体重构。每个问题独立修复，改动范围小，风险低，可逐步验证。

---

## 1. 全局中文化

所有菜单名改为中文，logo 保持不变。

| 原名 | 中文名 |
|------|--------|
| Dashboard | 仪表盘 |
| Projects | 项目管理 |
| PO | PO管理 |
| APK | APK管理 |
| Cases | 用例管理 |
| Scripts | 脚本管理 |
| Devices | 设备管理 |
| Tasks | 任务管理 |
| Keywords | 关键字管理 |
| Debug | 调试 |

涉及改动：
- 侧边栏菜单文本
- 所有页面 `<a-page-header>` 的 title/sub-title
- 所有表格列名
- 所有按钮文本
- 路由 name 属性可保持英文（内部使用），但菜单展示为中文

---

## 2. Dashboard 数据修复

当前问题：
- `stats.cases` 始终为 0（没有获取用例数量）
- 只在 `onMounted` 加载一次，不刷新
- 靠前端 `.length` 计数，没有专用统计 API

修复方案：
- 后端新增 `/api/stats` 统计 API，返回项目数、用例数、设备数、任务数
- 前端每次进入 Dashboard 页面时重新获取数据
- 标题改为"仪表盘"，所有标签中文化："项目数"、"用例数"、"设备数"、"任务数"、"近期任务"、"在线设备"

---

## 3. 删除项目二次确认

规则：
- 有关联数据 → 弹窗提示禁止删除："该项目下存在 N 个页面、N 个用例、N 个脚本，请先清除所有关联数据后再删除"
- 无关联数据 → 二次确认弹窗："确定删除项目「XXX」吗？删除后不可恢复"，确认后删除

涉及改动：
- 后端新增 `/api/projects/{id}/stats` 返回关联资源统计（页面数、用例数、脚本数）
- 前端删除按钮改为先调用 stats API，根据结果决定弹窗内容
- 有数据时弹窗只显示信息，无"确认删除"按钮
- 无数据时弹窗显示确认/取消按钮

---

## 4. 项目详情页修复

问题：
- "添加页面"按钮点了无效——没有对应的 Modal 组件
- "添加用例"按钮点了无效——没有对应的 Modal 组件
- 上传脚本后一直 loading——没有上传状态反馈

修复方案：
- 补充"添加页面" Modal：页面名称、描述、所属项目名（只读）
- 补充"添加用例" Modal：用例名称、类型（只有"关键字驱动"）、描述
- 修复脚本上传：上传中显示 loading 状态，成功 `message.success`，失败 `message.error`

---

## 5. PO管理弹窗内显示项目名

创建 Page Object 弹窗顶部加一条只读信息："所属项目：XXX"，从 `selectedProject` 对应的项目名称中取。

---

## 6. APK列表一直loading修复

排查方向：
- `APKPackageResponse` 中 `uploaded_at` 序列化问题——确保 Pydantic 正确将 datetime 转为 ISO 字符串
- 前端增加错误处理，API 请求失败时显示错误提示而非一直 loading
- 无 APK 数据时显示空列表而非卡在 loading

---

## 7. 用例管理修复

- 菜单名改为"用例管理"（侧边栏、路由路径可保持 `/cases`）
- 修复关键字加载：`getKeywordCategories` 返回 `[{category, count}]`，前端需提取 `.category` 字段作为分类名
- 确保所有关键字正确加载显示

---

## 8. 用例类型去掉脚本驱动

- 用例类型只保留"关键字驱动"选项
- 后端 TestCase model/schema 中 `type` 字段默认值设为 `keyword`
- 前端去掉"脚本驱动"选项

---

## 9. 脚本管理上传修复

脚本管理已有项目关联（顶部下拉框），无需改动关联逻辑。

修复上传反馈：
- 上传过程中显示 loading 状态
- 成功后 `message.success` 提示
- 失败后 `message.error` 提示

---

## 10. 设备管理简化

改动：
- 移除顶部"TCP/IP连接"按钮和对应弹窗
- USB设备操作列添加"连接"按钮
- 点击"连接"：平台自动执行 `adb tcpip 5555` 开放端口 → `adb connect <ip>:5555` 完成连接 → 成功后刷新设备列表
- TCP/IP设备操作列显示"断开"按钮（已有）
- 页面标题改为"设备管理"，所有中文化
- 后端新增一键连接 API `/api/devices/{serial}/connect`，自动完成端口开放和连接

---

## 11. 任务创建显示脚本和用例

改动：
- "测试用例"下拉框改为"测试内容"分组选择：
  - **用例组**：项目下所有关键字驱动用例，格式 `用例 - XXX`
  - **脚本组**：项目下所有脚本，格式 `脚本 - XXX`
- 不同类型使用不同执行器：
  - 选用例 → `AndroidExecutor` 执行，保存 `case_id`
  - 选脚本 → `ScriptExecutor` 执行，保存 `script_id`
- `TestTask` 模型增加 `script_id` 字段（与 `case_id` 互斥）
- `TaskDispatcher` 执行时根据 `case_id` 或 `script_id` 选择对应执行器
- 任务表格列改为"测试内容"，根据类型显示用例名或脚本名
- 增加"类型"列，标签区分"用例"和"脚本"
- 后端 `TestTaskCreate` schema 增加 `script_id` 字段（可选，与 `case_id` 互斥）

---

## 12. 关键字管理——自定义入口

自定义关键字是用户编写 Python 代码实现关键字逻辑，与内置关键字本质相同，只是由用户自己编写。

创建流程：
1. 页面增加"创建自定义关键字"按钮
2. 创建弹窗包含：
   - 关键字名称（必填）
   - 描述（必填）
   - 平台选择：all / android
   - **Python 代码编辑区**：用户编写关键字实现代码，提供代码模板和语法提示
   - 参数列表：从代码中自动提取或用户手动定义参数名和类型
3. 提交时：
   - **先校验 Python 格式/语法**——用 `ast.parse()` 或 `compile()` 验证，语法错误时拒绝保存并提示具体错误
   - 校验通过后，将代码写入 `custom_keyword.py` 模块文件
   - 动态加载该模块，注册新关键字到系统中

管理功能：
- 自定义关键字在列表中以 `custom` 分类标签显示（橙色）
- 支持"编辑"和"删除"操作
- 编辑时重新校验语法，通过后更新代码并重新动态加载
- 删除只允许 `custom` 分类关键字
- 保存后立即刷新列表，用例编排页面也能动态加载

后端需要：
- `PUT /api/keywords/{id}` — 编辑自定义关键字（含代码+参数）
- `DELETE /api/keywords/{id}` — 删除自定义关键字（只允许 custom 分类）
- 修改现有 `POST /api/projects/{project_id}/custom-keywords` 增加 code 字段
- `custom_keyword.py` 模块管理：代码写入、语法校验、动态加载

迁移路径：
- 后续可将成熟的自定义关键字迁移为内置关键字（开发者手动添加到 `KeywordEngine.BUILTIN_KEYWORDS` 和 `AndroidExecutor`）

---

## 13. 调试页面修复

改动：
- 所有文本中文化
- 确保 `uiautodev_manager.start()` 正确启动进程
- 确保 `get_device_url()` 返回正确的 iframe URL
- iframe 加载失败时显示错误提示而非空白
- 选择设备后，先检查 uiautodev 是否在运行，未运行时提示用户先启动

---

## 修改范围总览

### 前端文件
- `App.vue` / 侧边栏组件 — 中文化菜单
- `Dashboard.vue` — 数据修复 + 中文化
- `Projects.vue` — 删除二次确认（禁止有数据的删除）
- `ProjectDetail.vue` — 补充 Modal + 上传反馈
- `POManagement.vue` — 弹窗内显示项目名
- `APKManagement.vue` — loading修复 + 错误处理
- `TestCaseManagement.vue` — 关键字加载修复 + 去掉脚本类型 + 中文化
- `ScriptManagement.vue` — 上传反馈
- `Devices.vue` — 去掉TCP/IP弹窗，加连接按钮 + 中文化
- `Tasks.vue` — 分组选择用例/脚本 + 中文化
- `Keywords.vue` — 自定义关键字创建/编辑/删除 + 中文化
- `Debug.vue` — 中文化 + iframe错误提示
- `api/index.js` — 新增 API 调用

### 后端文件
- `main.py` — 注册新路由
- 新增 `api/stats.py` — 统计 API
- `api/projects.py` — 新增 stats 接口
- `api/devices.py` — 新增一键连接接口
- `api/keywords.py` — 新增编辑/删除接口，修改创建接口增加 code 字段
- `api/tasks.py` — 支持 script_id
- `models/test_task.py` — 增加 script_id 字段
- `schemas/test_task.py` — 增加 script_id 字段
- `core/task_dispatcher.py` — 根据 case_id/script_id 选择执行器
- 新增 `core/custom_keyword_loader.py` — 代码写入、语法校验、动态加载
- 数据库迁移：test_tasks 表增加 script_id 列

---

## 实施顺序建议

1. 全局中文化（1）— 贯穿所有页面，先做
2. Bug修复类（2, 4, 6, 7, 8, 9, 13）— 修复现有功能
3. 交互优化类（3, 5, 10）— 改善用户体验
4. 功能增强类（11, 12）— 新增功能，依赖前面的修复