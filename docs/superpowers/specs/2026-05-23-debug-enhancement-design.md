# 调试功能增强设计方案

**日期**: 2026-05-23
**版本**: v1.0
**状态**: 已完成

## 一、需求概述

本次调试功能增强包含以下需求：

| 序号 | 需求描述 | 优先级 |
|------|----------|--------|
| 1 | 修复调试页面iframe空白问题 | 高 |
| 2 | 修复设备管理TCP/IP设备离线显示问题 | 高 |
| 3 | 适配调试页面支持滚动显示完整内容 | 高 |
| 4 | 优化调试页面布局，合并工具栏 | 高 |
| 5 | iframe直接使用云端URL | 高 |

## 二、调试页面设计

### 2.1 布局结构

```
┌─────────────────────────────────────────────────────────┐
│  [运行中] 云端服务: uiauto2.devsleep.com      [选择设备▼]│
│  [加载设备] [加载主页] [新窗口打开] [刷新] [全屏]        │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│                                                         │
│                    iframe 区域                          │
│              (支持滚动，最小1024x768)                   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 2.2 iframe URL 策略

**修改前**：
- 使用代理路径 `/uiautodev/android/{serial}`
- 可能因跨域或代理配置导致空白

**修改后**：
- 直接使用完整云端 URL `https://uiauto2.devsleep.com/android/{serial}`
- 新窗口打开也使用相同 URL

## 三、设备管理优化设计

### 3.1 TCP/IP设备状态处理

**状态逻辑**：
```javascript
if (isTcpipDevice(device.serial)) {
  if (device.status === 'online') {
    // 显示"断开"按钮
  } else {
    // 显示"重连"按钮
  }
} else {
  // USB设备，显示"连接"或"离线"
}
```

### 3.2 重连功能实现

**后端API**：
```python
POST /api/devices/connect
Body: { ip: string, port: number }
```

**前端调用**：
```javascript
const handleReconnect = async (device) => {
  const [ip, port] = device.serial.split(':')
  await connectDevice(ip, parseInt(port) || 5555)
  message.success('重连成功')
  fetchDevices()
}
```

## 四、页面适配设计

### 4.1 响应式布局

**CSS策略**：
```css
.debug {
  overflow: auto;
  min-width: 0;
}

.iframe-container {
  overflow: auto;
}

.iframe-container iframe {
  min-width: 1024px;
  min-height: 768px;
}
```

### 4.2 高度计算

```javascript
const updateHeight = () => {
  iframeHeight.value = Math.max(window.innerHeight - 160, 500)
}
```

## 五、实施步骤

### Step 1: 调试页面修复
- 修改 Debug.vue 移除未定义变量
- 修复模板结构错误
- 修改 iframe 直接使用云端 URL

### Step 2: 设备管理优化
- 修改 Devices.vue 添加重连按钮逻辑
- 优化TCP/IP设备状态显示
- 测试设备连接和重连功能

### Step 3: 页面适配优化
- 调整 Debug.vue 样式
- 添加滚动支持
- 优化 iframe 显示

### Step 4: 测试验证
- 测试调试页面iframe加载
- 测试设备管理功能
- 测试页面滚动适配

## 六、验收标准

| 功能 | 验收标准 |
|------|----------|
| 调试页面 | iframe能正常加载云端服务，无空白 |
| 设备管理 | TCP/IP设备在线显示"断开"，离线显示"重连" |
| 页面适配 | 支持滚动，内容完整显示 |
| 新窗口打开 | 能在新标签页正常打开调试页面 |

## 七、风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| iframe跨域限制 | 页面无法加载 | 使用新窗口打开作为备选方案 |
| 云端服务不可用 | 调试功能失效 | 保持本地uiautodev支持 |
| 设备重连失败 | 用户体验差 | 提供清晰的错误提示 |
