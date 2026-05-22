# UI AutoTest Platform 前端功能补全设计

**日期**: 2026-05-18
**范围**: 前端缺失功能一次性补全 + 后端模型/API扩展

---

## Context

当前平台前端严重缺失核心功能：
- 测试用例没有创建入口（只有空按钮，没有关键字+元素+参数的步骤编排UI）
- Tasks 创建无法工作（没有弹窗、没有选case/设备交互）
- 没有 APK 包管理（模型、API、UI 全缺）
- 没有 PO 管理独立入口（藏在项目详情tab里，没有独立的元素管理）
- 脚本管理没有独立页面
- 设备管理缺少 TCP/IP 连接功能

核心场景：Android App 自动化测试，基于关键字+PO设计模式。

---

## 1. 导航与菜单

从6个菜单扩展到10个，按逻辑分组：

```
侧边栏:
  ┌── 项目管理 ──┤
  │  Dashboard
  │  Projects
  │  PO管理       ← 新增独立菜单
  │  APK管理      ← 新增独立菜单
  │  测试用例     ← 新增独立菜单
  │  脚本管理     ← 新增独立菜单（从ProjectDetail移出）
  │
  ┌── 执行管理 ──┤
  │  Devices      ← 增强：TCP/IP连接
  │  Tasks        ← 修复：创建功能
  │
  ┌── 辅助 ──────┤
  │  Keywords
  │  Debug
```

**新增路由**:
- `/po` → PO管理页面
- `/apk` → APK管理页面
- `/cases` → 测试用例页面
- `/scripts` → 脚本管理页面

**共同模式**: APK管理、测试用例、脚本管理、PO管理页面顶部都有**项目选择器**（下拉框），切换后显示该项目下的数据。

---

## 2. 数据模型变更

### 2.1 新增模型：APKPackage

```
APKPackage:
├── id            (String, PK, 默认 apk_{uuid.hex[:8]})
├── project_id    (String, FK → projects.id, 必填)
├── version       (String, 必填, 如 "2.1.0")
├── file_path     (String, 必填, APK存储路径)
├── file_size     (Integer, 文件大小bytes)
├── package_name  (String, APK包名, 如com.example.app)
├── uploaded_at   (DateTime, 上传时间)
├── description   (String, 可选, 版本备注)
```

**关系**: 一个 Project 有多个 APKPackage（版本列表），没有"当前版本"概念。

### 2.2 修改模型：TestTask（增加可选apk_id）

```
TestTask (现有字段 + 新增):
├── apk_id        (String, 可选, FK → apk_packages.id)
                  可选填，为空表示不自动安装APK
                  填了表示任务开始时先安装指定APK版本
```

### 2.3 修改模型：TestCase（增加depends_on）

```
TestCase (现有字段 + 新增):
├── depends_on    (String, 可选, FK → test_cases.id)
                  依赖的前置用例ID
                  执行时先跑depends_on用例，再跑本用例
                  依赖用例失败 → 当前用例跳过(skipped)
```

### 2.4 新增关键字：install_apk

```
种子数据新增:
├── "install_apk"  (category: platform, platform: android)
│      params: {"apk_id": {"type": "string"}}
│      description: "安装指定APK到设备"
```

---

## 3. 新增后端API

### APK管理
```
GET    /api/projects/{id}/apks                    → 列出项目所有APK版本
POST   /api/projects/{id}/apks                    → 上传新APK（multipart/form-data）
DELETE /api/projects/{id}/apks/{apk_id}           → 删除APK版本
GET    /api/projects/{id}/apks/{apk_id}           → 获取APK详情
```

### 测试用例（补充前端需要的）
```
PUT    /api/projects/{id}/cases/{case_id}         → 更新用例（含步骤更新）
DELETE /api/projects/{id}/cases/{case_id}         → 删除用例
POST   /api/projects/{id}/cases/{case_id}/steps/{step_id} → 更新步骤
```

### 设备TCP/IP
```
POST   /api/devices/tcpip                         → adb tcpip切换（参数: serial, port=5555）
POST   /api/devices/connect                       → adb connect（参数: ip, port）
POST   /api/devices/disconnect                    → adb disconnect（参数: ip, port）
```

---

## 4. 前端页面设计

### 4.1 PO管理页面

**功能**: 项目选择器 + Page Object列表 + 元素CRUD

**交互**:
- 项目选择器（下拉框切换项目）
- Page Object列表（名称、描述、元素数量）
- 点击展开显示该PO下的元素列表
- 创建PO弹窗：名称 + 描述
- 创建元素弹窗：名称 + 定位方式(id/xpath/class/accessibility_id/text/uiautomator) + 定位值 + 描述
- 编辑/删除PO和元素

**API调用**: getPages, createPage, updatePage, deletePage, getElements, createElement, updateElement, deleteElement

### 4.2 APK管理页面

**功能**: 项目选择器 + APK版本列表 + 上传/删除

**交互**:
- 项目选择器
- APK版本表格：版本号、包名、大小、上传时间、操作(删除)
- 上传弹窗：拖拽上传APK文件，版本号（自动从APK解析或手动填写），备注
- 上传时后端用 `aapt dump badging` 解析包名和版本，前端预填

**API调用**: 新增APK相关API

### 4.3 测试用例页面（核心重点）

**功能**: 项目选择器 + 用例列表 + 拖拽编排创建/编辑用例

**用例列表**:
- 表格：名称、类型(keyword/script)、步骤数、前置用例、创建时间、操作(编辑/删除)
- 创建按钮 → 进入编排模式

**编排模式（创建/编辑用例）**:
- 左栏：关键字库（按category分组：basic/platform/custom），每个关键字旁有⊕添加按钮，顶部有搜索框
- 右栏：步骤编排区
  - 用例名、描述、前置用例（下拉框选其他用例，可选）
  - 步骤列表：每步显示关键字名 + 元素名 + 参数值
  - 每步可编辑：选关键字→根据关键字参数定义动态显示参数输入框→选元素（下拉框按PO分组）
  - 步骤排序（↑↓按钮）、删除（×按钮）
  - [+ 添加空步骤] 按钮
- 保存按钮提交完整用例数据

**数据提交格式**:
```json
{
  "name": "登录测试",
  "type": "keyword",
  "description": "测试登录流程",
  "depends_on": "tc_xxxx",
  "steps": [
    {"keyword_id": "kw_launch_app", "po_element_id": null, "params": {"package": "com.example.app"}, "step_order": 1},
    {"keyword_id": "kw_input", "po_element_id": "ele_xxxx", "params": {"text": "username"}, "step_order": 2},
    {"keyword_id": "kw_click", "po_element_id": "ele_yyyy", "params": {}, "step_order": 3}
  ]
}
```

### 4.4 脚本管理页面

**功能**: 项目选择器 + 脚本列表 + 上传/删除/查看详情

**交互**:
- 项目选择器
- 脚本表格：名称、类型、类/方法、上传时间、操作
- 上传按钮：拖拽上传.py文件
- 点击行展开详情：文件路径、解析出的类和方法列表
- 删除按钮

**API调用**: getScripts, uploadScript, deleteScript（已有）

### 4.5 Tasks页面（修复创建功能）

**功能**: 任务列表 + 创建任务弹窗 + 执行

**创建任务弹窗**:
- 测试用例：下拉框选项目下的用例
- APK版本：下拉框，选项= [不安装] + 项目所有APK版本
- 目标设备：多选checkbox，只显示online设备
- 创建后状态pending，点击Execute执行

**执行逻辑**:
- 如果Task有apk_id → 先安装APK到目标设备
- 如果用例有depends_on → 先执行前置用例
- 然后执行当前用例的步骤

### 4.6 Devices页面（增强TCP/IP）

**新增功能**:
- TCP/IP连接弹窗：
  - 显示当前USB连接的设备列表（供选择）
  - IP地址输入框 + 端口输入框（默认5555）
  - [切换到TCP/IP模式] 按钮 → 对选中USB设备执行 `adb tcpip {port}`
  - [连接设备] 按钮 → 执行 `adb connect {ip}:{port}`
- 断开按钮 → 对TCP/IP设备执行 `adb disconnect {ip}:{port}`
- 扫描按钮自动检测USB和TCP/IP设备

---

## 5. 不改的部分

- Dashboard页面（已有，只读统计）
- Keywords页面（已有，列表浏览）
- Debug页面（已有，uiautodev）
- Projects列表页面（已有，创建/删除项目）
- 后端模型：TestCase/CaseStep/Keyword/Element/PageObject/Script — 数据结构已完整
- 后端API：projects/pages/keywords/cases/scripts — 大部分已有，只需小补

---

## 6. 验证方式

1. 启动后端 `python main.py`
2. 启动前端 `cd frontend && npm run dev`（或直接访问 localhost:8000）
3. 逐页面验证：
   - PO管理：创建PO → 创建元素 → 列表显示正确
   - APK管理：上传APK → 解析包名 → 版本列表显示
   - 测试用例：拖拽编排创建用例 → 保存 → 列表显示 → 设置依赖
   - 脚本管理：上传脚本 → 解析类方法 → 列表显示
   - Devices：USB扫描 → TCP/IP连接 → 断开
   - Tasks：创建任务（选用例+APK+设备）→ 执行 → 状态更新