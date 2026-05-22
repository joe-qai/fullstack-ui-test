# 平台重构设计方案

**日期**: 2026-05-22
**版本**: v1.0
**状态**: 已完成

## 一、需求概述

本次重构包含以下核心需求：

| 序号 | 需求描述 | 优先级 |
|------|----------|--------|
| 1 | 完成对象管理：支持页面对象及元素编辑 | 高 |
| 2 | 菜单结构重构：资源管理、对象管理、执行中心 | 高 |
| 3 | 术语统一：关键字参数中的"事件"改为"对象" | 高 |
| 4 | 关键字排序：按 basic/platform/assertion 顺序 | 高 |
| 5 | Landing Page 重构：简洁的项目介绍 | 高 |
| 6 | 对象管理升为一级菜单 | 高 |

## 二、菜单结构设计

### 2.1 最终菜单结构

```
UiTesting
├── 仪表盘
├── 资源管理
│   ├── 项目管理
│   ├── APK管理
│   └── 设备管理
├── 关键字管理
├── 对象管理
├── 用例脚本
│   ├── 用例管理
│   ├── 脚本管理
│   └── 在线调试
└── 执行中心
    ├── 任务管理
    └── 报告管理
```

### 2.2 前端路由配置

```javascript
const routes = [
  { path: '/', name: 'Dashboard', component: Dashboard },
  { path: '/projects', name: 'Projects', component: Projects },
  { path: '/apks', name: 'APKs', component: APKManagement },
  { path: '/devices', name: 'Devices', component: Devices },
  { path: '/keywords', name: 'Keywords', component: Keywords },
  { path: '/po', name: 'PO', component: POManagement },
  { path: '/cases', name: 'Cases', component: Cases },
  { path: '/scripts', name: 'Scripts', component: ScriptManagement },
  { path: '/debug', name: 'Debug', component: Debug },
  { path: '/tasks', name: 'Tasks', component: Tasks },
  { path: '/reports', name: 'Reports', component: Reports },
]
```

## 三、对象管理设计

### 3.1 功能需求

- 编辑页面信息
- 管理页面下的元素（对象）
- 支持新增、编辑、删除页面元素
- 支持查看完整的页面对象树

### 3.2 前端界面设计

**页面列表**：
- 显示项目下的所有页面
- 点击展开查看页面下的元素
- 支持新增、编辑、删除页面

**元素管理**：
- 点击页面展开元素列表
- 支持新增、编辑、删除元素
- 元素字段：名称、定位方式、定位值、描述

## 四、术语统一设计

### 4.1 关键字参数

**修改前**：
- 事件对象
- 事件名称

**修改后**：
- 页面对象
- 对象名称

### 4.2 涉及文件

- `views/Cases.vue`：用例编辑时的参数标签
- `views/Keywords.vue`：关键字参数定义
- `views/POManagement.vue`：元素管理界面

## 五、关键字排序设计

### 5.1 排序规则

```javascript
const categoryOrder = ['basic', 'platform', 'assertion']

keywords.sort((a, b) => {
  const orderA = categoryOrder.indexOf(a.category)
  const orderB = categoryOrder.indexOf(b.category)
  if (orderA !== orderB) return orderA - orderB
  return a.name.localeCompare(b.name)
})
```

### 5.2 前端显示

- 左侧关键字分组显示
- 按 basic/platform/assertion 顺序排列
- 组内按名称字母顺序

## 六、Landing Page 设计

### 6.1 页面内容

```html
<div class="landing">
  <header>
    <h1>UiTesting</h1>
    <p>开源多端UI自动化测试平台</p>
  </header>
  
  <section class="features">
    <h2>核心功能</h2>
    <div class="feature-grid">
      <div class="feature">关键字驱动测试</div>
      <div class="feature">页面对象模型</div>
      <div class="feature">多设备并行执行</div>
      <div class="feature">可视化调试界面</div>
    </div>
  </section>
  
  <section class="quickstart">
    <h2>快速开始</h2>
    <code>cd backend &amp;&amp; python main.py</code>
    <code>cd frontend &amp;&amp; npm run dev</code>
  </section>
  
  <footer>
    <a href="https://github.com/joe-qai/fullstack-ui-test">GitHub</a>
  </footer>
</div>
```

## 七、实施步骤

### Step 1: 菜单结构重构
- 修改 `App.vue` 更新菜单结构
- 调整路由配置
- 更新菜单图标和标签

### Step 2: 对象管理功能完善
- 修改 `POManagement.vue` 支持元素编辑
- 添加展开/收起功能
- 优化页面布局

### Step 3: 术语统一
- 全局搜索并替换"事件"为"对象"
- 更新所有相关组件

### Step 4: 关键字排序
- 修改 `Cases.vue` 关键字显示逻辑
- 添加分组排序功能

### Step 5: Landing Page 重构
- 修改 `index.html` 简化内容
- 保留GitHub链接

## 八、验收标准

| 功能 | 验收标准 |
|------|----------|
| 菜单结构 | 资源管理、对象管理、执行中心正确显示 |
| 对象管理 | 支持编辑页面和元素，支持展开查看 |
| 术语统一 | 所有"事件"改为"对象"，界面一致 |
| 关键字排序 | 按 basic/platform/assertion 顺序显示 |
| Landing Page | 简洁美观，包含GitHub链接 |

## 九、风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| 术语替换遗漏 | 用户混淆 | 完整的代码审查和测试 |
| 菜单结构调整破坏路由 | 页面无法访问 | 先测试路由再合并 |
| 对象管理功能复杂 | 开发周期长 | 分阶段实施，先MVP后优化 |
