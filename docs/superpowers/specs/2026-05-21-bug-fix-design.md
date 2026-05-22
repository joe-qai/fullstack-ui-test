# 问题修复设计方案

**日期**: 2026-05-21
**版本**: v1.0
**状态**: 待评审

## 一、问题概述

根据问题清单，需要修复以下5个问题：

| 序号 | 问题描述 | 优先级 |
|------|----------|--------|
| 1 | 创建项目接口500错误，需要支持名称、描述和状态字段 | 高 |
| 2 | 上传APK包必定500错误 | 高 |
| 3 | 设备管理：已TCP/IP连接的设备再次点击需提示已连接 | 高 |
| 4 | 任务管理：新增任务时设备列表未正确加载 | 高 |
| 5 | 关键字管理：自定义关键字编辑器需要支持Python语法 | 高 |

## 二、详细设计

### 2.1 问题1：创建项目接口修复

**需求**:
- 创建项目不需要选择状态，创建成功默认启用
- 列表显示状态及操作禁用/启用

**数据库修改** (models/project.py):
```python
class Project(Base):
    __tablename__ = "projects"
    id = Column(String, primary_key=True, default=lambda: f"proj_{uuid.uuid4().hex[:8]}")
    name = Column(String, nullable=False)
    description = Column(String)      # 新增：备注描述
    status = Column(String, default="enabled")  # 新增：状态(enabled/disabled)
    created_at = Column(DateTime, default=utc_now)
```

**API修改** (api/projects.py):
- POST `/api/projects`: 创建项目时默认设置status="enabled"
- PUT `/api/projects/{id}`: 支持更新status字段

**前端修改** (views/Projects.vue):
- 创建弹窗：移除状态选择，仅保留名称和描述
- 列表页：显示状态标签（启用/禁用）
- 添加启用/禁用操作按钮

### 2.2 问题2：上传APK包500错误修复

**需求**: 上传APK必定500，需要检查端口配置和数据库操作

**问题分析**:
1. 前端API请求端口可能与后端服务端口不一致
2. 数据库操作可能存在错误

**修复方案**:

**前端配置检查** (vite.config.js):
```javascript
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:5175',  // 确保与后端端口一致
        changeOrigin: true
      }
    }
  }
})
```

**后端配置检查** (config.py):
- 确保 `apks_dir` 目录存在且可写
- 确保数据库连接正常

**APK上传接口修复** (api/apks.py):
- 添加完整的异常处理
- 添加文件大小限制（如50MB）
- 添加文件类型校验

### 2.3 问题3：设备连接逻辑修复

**需求**:
- 已TCP/IP连接的设备，后端需要明确返回状态
- 离线及未TCP/IP连接的设备，点击连接即提示连接成功或失败

**后端修改** (api/devices.py):
```python
@router.post("/devices/{serial}/connect")
def connect_device_one_click(serial: str, db: Session = Depends(get_db)):
    # 检查是否已通过TCP/IP连接
    tcpip_device = db.query(Device).filter(
        Device.serial.like(f"%:{serial.split(':')[0]}") | 
        Device.serial.like(f"{serial.split(':')[0]}:%")
    ).first()
    
    if tcpip_device and tcpip_device.status == "online":
        raise HTTPException(status_code=400, detail=f"设备已通过 TCP/IP 连接: {tcpip_device.serial}")
    
    # 检查当前设备状态
    current_device = db.query(Device).filter(Device.serial == serial).first()
    if current_device and current_device.status != "online":
        raise HTTPException(status_code=400, detail="设备当前离线，无法进行 TCP/IP 连接")
    
    # 执行连接逻辑
    ...
```

**前端修改** (views/Devices.vue):
- 根据后端返回状态显示不同提示
- 已连接设备显示"已连接"状态

### 2.4 问题4：任务管理设备加载修复

**需求**:
- 新增任务时，弹窗需要加载目标设备
- 需要带上标签显示在线或离线

**前端修改** (views/Tasks.vue):
```javascript
const openCreateModal = async () => {
  taskForm.value = { projectId: null, content_id: null, apk_id: null, device_ids: [] }
  showCreateModal.value = true
  try {
    const [projRes, devRes] = await Promise.all([getProjects(), getDevices()])
    projects.value = projRes.data
    devices.value = devRes.data  // 确保设备列表正确加载
  } catch (error) {
    console.error('Failed to load modal data:', error)
  }
}
```

**设备选择界面**:
```
目标设备（多选）:
☑ 设备1 [在线]
☑ 设备2 [离线]
☐ 设备3 [在线]
```

### 2.5 问题5：关键字管理Python语法支持

**需求**:
- 编辑器需要直接支持Python语法
- 支持手动编写def方法

**后端修改** (core/custom_keyword_loader.py):
```python
def validate_code(code: str):
    """Validate Python code syntax using ast.parse."""
    try:
        ast.parse(code)
        # 检查是否包含函数定义
        tree = ast.parse(code)
        has_function = False
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                has_function = True
                break
        if not has_function:
            return False, "代码中需要包含至少一个函数定义"
        return True, ""
    except SyntaxError as e:
        line_info = f"第 {e.lineno} 行" if e.lineno else ""
        return False, f"语法错误 {line_info}: {e.msg}"
```

**前端修改** (views/Keywords.vue):
- 增大代码编辑区域
- 添加Python语法提示
- 添加代码示例模板

## 三、实施步骤

### Step 1: 项目模型修复
- 修改 `models/project.py` 添加 description 和 status 字段
- 修改 `schemas/project.py` 更新数据结构
- 修改 `api/projects.py` 更新创建和更新逻辑

### Step 2: 项目前端修复
- 修改 `views/Projects.vue` 更新创建弹窗和列表显示

### Step 3: APK上传修复
- 检查并修复 `vite.config.js` 代理配置
- 添加异常处理和文件校验

### Step 4: 设备连接逻辑修复
- 修改 `api/devices.py` 添加连接状态检查
- 修改 `views/Devices.vue` 显示连接状态

### Step 5: 任务管理设备加载修复
- 修改 `views/Tasks.vue` 确保设备列表正确加载

### Step 6: 关键字管理修复
- 修改 `core/custom_keyword_loader.py` 优化语法验证
- 修改 `views/Keywords.vue` 优化代码编辑器

## 四、验收标准

| 问题 | 验收标准 |
|------|----------|
| 1 | 创建项目成功，默认启用，列表显示状态，可禁用/启用 |
| 2 | 上传APK成功，无500错误，正确解析包名和版本 |
| 3 | 已连接设备提示"已连接"，离线设备提示"离线" |
| 4 | 新增任务时设备列表正常加载，显示在线/离线标签 |
| 5 | 自定义关键字支持完整Python语法，能编写def方法 |

## 五、风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| 数据库字段修改失败 | 项目创建失败 | 备份数据库，测试迁移脚本 |
| 端口配置不一致 | API请求失败 | 统一使用环境变量管理端口 |
| Python代码注入 | 安全风险 | 严格的语法验证，沙箱执行环境 |