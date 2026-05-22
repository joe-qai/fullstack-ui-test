# MultiUiAutoTest 平台问题修复实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 逐项修复平台 13 个已知问题，包括全局中文化、Dashboard 数据、项目删除确认、用例类型精简、设备管理简化、任务创建支持脚本、自定义关键字管理。

**Architecture:** 采用逐项修复策略，每个问题独立修改，改动范围小，风险低。后端新增统计 API、一键连接 API、自定义关键字管理模块；前端统一中文化、修复缺失 Modal、增加上传反馈、支持用例/脚本分组选择。

**Tech Stack:** Vue 3 + Ant Design Vue (前端), FastAPI + SQLAlchemy + SQLite (后端), pytest (测试)

---

## 文件结构总览

### 前端修改（已有文件）
- `frontend/src/App.vue` — 侧边栏菜单中文化
- `frontend/src/api/index.js` — 新增 API 调用
- `frontend/src/views/Dashboard.vue` — 数据修复 + 中文化
- `frontend/src/views/Projects.vue` — 删除二次确认 + 中文化
- `frontend/src/views/ProjectDetail.vue` — 补充 Modal + 上传反馈 + 中文化
- `frontend/src/views/POManagement.vue` — 弹窗内显示项目名
- `frontend/src/views/APKManagement.vue` — loading 修复 + 错误处理
- `frontend/src/views/TestCaseManagement.vue` — 关键字加载修复 + 去掉脚本类型
- `frontend/src/views/ScriptManagement.vue` — 上传反馈
- `frontend/src/views/Devices.vue` — 去掉 TCP/IP 弹窗，加连接按钮 + 中文化
- `frontend/src/views/Tasks.vue` — 分组选择用例/脚本 + 中文化
- `frontend/src/views/Keywords.vue` — 自定义关键字创建/编辑/删除 + 中文化
- `frontend/src/views/Debug.vue` — 中文化 + iframe 错误提示

### 后端新建文件
- `backend/api/stats.py` — 统计 API
- `backend/core/custom_keyword_loader.py` — 自定义关键字代码写入、语法校验、动态加载
- `backend/tests/test_stats.py` — 统计 API 测试
- `backend/tests/test_custom_keywords.py` — 自定义关键字测试
- `backend/tests/test_tasks_script.py` — 任务 script_id 测试

### 后端修改文件
- `backend/api/__init__.py` — 注册 stats 路由
- `backend/api/projects.py` — 新增 `/{id}/stats` 接口
- `backend/api/devices.py` — 新增 `/{serial}/connect` 接口
- `backend/api/keywords.py` — 新增 PUT/DELETE，修改 POST 增加 code 字段
- `backend/api/tasks.py` — 支持 script_id，验证 case_id/script_id 互斥
- `backend/models/test_task.py` — 增加 script_id 字段，case_id 改为 nullable
- `backend/schemas/test_task.py` — 增加 script_id 字段
- `backend/models/keyword.py` — 增加 code 字段
- `backend/schemas/keyword.py` — 增加 code 字段
- `backend/core/task_dispatcher.py` — 根据 case_id/script_id 选择执行器
- `backend/executors/android_executor.py` — 支持自定义关键字动态执行
- `backend/executors/script_executor.py` — 添加 `run_script` 方法
- `backend/db/init_db.py` — 初始化 custom_keywords 目录

---

## Phase 1: 全局中文化

### Task 1: App.vue 侧边栏菜单中文化

**Files:**
- Modify: `frontend/src/App.vue:13-52`

- [ ] **Step 1: 修改菜单文本**

将仍显示英文的菜单项改为中文。当前已有中文的不动（PO管理、APK管理、脚本管理、测试用例）。

```vue
        <a-menu-item key="dashboard">
          <DashboardOutlined />
          <span>仪表盘</span>
        </a-menu-item>
        <a-menu-item key="projects">
          <ProjectOutlined />
          <span>项目管理</span>
        </a-menu-item>
        <!-- PO管理 和 APK管理 已是中文，跳过 -->
        <!-- 测试用例 已是中文，跳过 -->
        <!-- 脚本管理 已是中文，跳过 -->
        <a-menu-item key="devices">
          <MobileOutlined />
          <span>设备管理</span>
        </a-menu-item>
        <a-menu-item key="tasks">
          <PlayCircleOutlined />
          <span>任务管理</span>
        </a-menu-item>
        <a-menu-item key="keywords">
          <KeyOutlined />
          <span>关键字管理</span>
        </a-menu-item>
        <a-menu-item key="debug">
          <BugOutlined />
          <span>调试</span>
        </a-menu-item>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/App.vue
git commit -m "feat(i18n): localize sidebar menu to Chinese"
```

---

### Task 2: Dashboard.vue 中文化 + 数据修复

**Files:**
- Create: `backend/api/stats.py`
- Modify: `backend/api/__init__.py`
- Modify: `frontend/src/views/Dashboard.vue`
- Modify: `frontend/src/api/index.js`
- Test: `backend/tests/test_stats.py`

- [ ] **Step 1: 编写统计 API（先写测试）**

创建 `backend/tests/test_stats.py`：

```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_get_stats():
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "projects" in data
    assert "cases" in data
    assert "devices" in data
    assert "tasks" in data
    assert isinstance(data["projects"], int)
    assert isinstance(data["cases"], int)
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd backend && pytest tests/test_stats.py -v
```

Expected: `FAIL` — `404 Not Found` (路由未注册)

- [ ] **Step 3: 实现统计 API**

创建 `backend/api/stats.py`：

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.database import get_db
from models.project import Project
from models.test_case import TestCase
from models.device import Device
from models.test_task import TestTask

router = APIRouter(prefix="/api", tags=["stats"])


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    return {
        "projects": db.query(Project).count(),
        "cases": db.query(TestCase).count(),
        "devices": db.query(Device).count(),
        "tasks": db.query(TestTask).count(),
    }
```

修改 `backend/api/__init__.py`，在 `api_router.include_router(apks_router)` 后新增：

```python
from api.stats import router as stats_router
api_router.include_router(stats_router)
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd backend && pytest tests/test_stats.py -v
```

Expected: `PASS`

- [ ] **Step 5: 修改前端 Dashboard 调用统计 API + 中文化**

修改 `frontend/src/api/index.js`，在文件末尾添加：

```javascript
// Stats
export const getStats = () => api.get('/api/stats')
```

修改 `frontend/src/views/Dashboard.vue`，替换整个 `<template>` 和 `<script setup>`：

```vue
<template>
  <div class="dashboard">
    <a-page-header title="仪表盘" sub-title="UI 自动化测试平台" />

    <a-row :gutter="[16, 16]" style="margin-top: 24px">
      <a-col :span="6">
        <a-card>
          <a-statistic title="项目数" :value="stats.projects" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="用例数" :value="stats.cases" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="设备数" :value="stats.devices" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="任务数" :value="stats.tasks" />
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="[16, 16]" style="margin-top: 24px">
      <a-col :span="12">
        <a-card title="近期任务">
          <a-list :data-source="recentTasks" :loading="loading">
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta
                  :title="item.id"
                  :description="`状态: ${item.status}`"
                />
              </a-list-item>
            </template>
          </a-list>
        </a-card>
      </a-col>
      <a-col :span="12">
        <a-card title="在线设备">
          <a-list :data-source="onlineDevices" :loading="loading">
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta
                  :title="item.name || item.serial"
                  :description="`平台: ${item.platform}`"
                />
              </a-list-item>
            </template>
          </a-list>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getStats, getDevices, getTasks } from '../api'

const stats = ref({ projects: 0, cases: 0, devices: 0, tasks: 0 })
const recentTasks = ref([])
const onlineDevices = ref([])
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const [statsRes, devicesRes, tasksRes] = await Promise.all([
      getStats(),
      getDevices(),
      getTasks(),
    ])
    stats.value = statsRes.data
    recentTasks.value = tasksRes.data.slice(0, 5)
    onlineDevices.value = devicesRes.data.filter(d => d.status === 'online')
  } catch (error) {
    console.error('Failed to fetch dashboard data:', error)
  } finally {
    loading.value = false
  }
})
</script>
```

- [ ] **Step 6: 启动前后端验证**

Terminal 1:
```bash
cd backend && python main.py
```

Terminal 2:
```bash
cd frontend && npm run dev
```

浏览器访问 `http://localhost:5173/dashboard`，确认：
- 页面标题显示"仪表盘"
- 四个统计卡片显示正确数字（项目数、用例数、设备数、任务数）
- "近期任务"和"在线设备"列表正常显示

- [ ] **Step 7: Commit**

```bash
git add backend/api/stats.py backend/api/__init__.py backend/tests/test_stats.py frontend/src/views/Dashboard.vue frontend/src/api/index.js
git commit -m "feat: add stats API and fix dashboard data + Chinese localization"
```

---

### Task 3: Projects.vue 中文化 + 删除二次确认框架

**Files:**
- Modify: `frontend/src/views/Projects.vue`

- [ ] **Step 1: 中文化 + 增加确认弹窗结构**

替换整个 `frontend/src/views/Projects.vue`：

```vue
<template>
  <div class="projects">
    <a-page-header
      title="项目管理"
      sub-title="管理你的测试项目"
    >
      <template #extra>
        <a-button type="primary" @click="showModal = true">创建项目</a-button>
      </template>
    </a-page-header>

    <a-table
      :columns="columns"
      :data-source="projects"
      :loading="loading"
      row-key="id"
      style="margin-top: 24px"
    >
      <template #action="{ record }">
        <a-button type="link" @click="viewProject(record.id)">查看</a-button>
        <a-button type="link" danger @click="onDeleteClick(record)">删除</a-button>
      </template>
    </a-table>

    <a-modal
      v-model:open="showModal"
      title="创建项目"
      @ok="handleCreate"
    >
      <a-form :model="form" layout="vertical">
        <a-form-item label="名称" required>
          <a-input v-model:value="form.name" />
        </a-form-item>
        <a-form-item label="App ID">
          <a-input v-model:value="form.app_id" />
        </a-form-item>
        <a-form-item label="平台">
          <a-select v-model:value="form.platform">
            <a-select-option value="android">Android</a-select-option>
            <a-select-option value="ios">iOS</a-select-option>
            <a-select-option value="web">Web</a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 删除确认弹窗 -->
    <a-modal
      v-model:open="showDeleteModal"
      :title="deleteModalTitle"
      :ok-button-props="deleteOkProps"
      @ok="handleDeleteConfirm"
      @cancel="showDeleteModal = false"
    >
      <p>{{ deleteModalContent }}</p>
    </a-modal>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { getProjects, createProject, deleteProject as deleteProjectApi } from '../api'

const router = useRouter()
const projects = ref([])
const loading = ref(false)
const showModal = ref(false)
const form = ref({ name: '', app_id: '', platform: 'android' })

const columns = [
  { title: '项目名称', dataIndex: 'name', key: 'name' },
  { title: 'App ID', dataIndex: 'app_id', key: 'app_id' },
  { title: '平台', dataIndex: 'platform', key: 'platform' },
  { title: '创建时间', dataIndex: 'created_at', key: 'created_at' },
  { title: '操作', key: 'action', slots: { customRender: 'action' } },
]

const showDeleteModal = ref(false)
const deleteModalTitle = ref('')
const deleteModalContent = ref('')
const deleteOkProps = ref({})
const pendingDeleteId = ref(null)
const pendingDeleteHasData = ref(false)

const fetchProjects = async () => {
  loading.value = true
  try {
    const res = await getProjects()
    projects.value = res.data
  } catch (error) {
    console.error('Failed to fetch projects:', error)
  } finally {
    loading.value = false
  }
}

const handleCreate = async () => {
  try {
    await createProject(form.value)
    showModal.value = false
    form.value = { name: '', app_id: '', platform: 'android' }
    fetchProjects()
  } catch (error) {
    console.error('Failed to create project:', error)
  }
}

const viewProject = (id) => {
  router.push(`/projects/${id}`)
}

const onDeleteClick = (record) => {
  // 占位：后续 Task 13 会接入 stats API
  // 临时逻辑：直接弹确认窗
  pendingDeleteId.value = record.id
  pendingDeleteHasData.value = false
  deleteModalTitle.value = '确认删除'
  deleteModalContent.value = `确定删除项目「${record.name}」吗？删除后不可恢复。`
  deleteOkProps.value = { danger: true }
  showDeleteModal.value = true
}

const handleDeleteConfirm = async () => {
  if (pendingDeleteHasData.value) {
    showDeleteModal.value = false
    return
  }
  try {
    await deleteProjectApi(pendingDeleteId.value)
    showDeleteModal.value = false
    fetchProjects()
  } catch (error) {
    console.error('Failed to delete project:', error)
  }
}

fetchProjects()
</script>

<style scoped>
.projects {
  padding: 24px;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/Projects.vue
git commit -m "feat(i18n): localize Projects page and add delete modal structure"
```

---

### Task 4: ProjectDetail.vue 中文化 + Modal 补充 + 上传反馈

**Files:**
- Modify: `frontend/src/views/ProjectDetail.vue`

- [ ] **Step 1: 添加"添加页面"Modal + "添加用例"Modal + 上传反馈**

替换整个 `frontend/src/views/ProjectDetail.vue`：

```vue
<template>
  <div class="project-detail">
    <a-page-header
      :title="project?.name || '项目详情'"
      sub-title="管理项目详情"
      @back="goBack"
    />

    <a-tabs v-model:activeKey="activeKey" style="margin-top: 24px">
      <a-tab-pane key="pages" tab="页面">
        <a-button type="primary" @click="showPageModal = true" style="margin-bottom: 16px">
          添加页面
        </a-button>
        <a-list :data-source="pages" row-key="id">
          <template #renderItem="{ item }">
            <a-list-item>
              <a-list-item-meta
                :title="item.name"
                :description="item.description"
              />
            </a-list-item>
          </template>
        </a-list>
      </a-tab-pane>

      <a-tab-pane key="cases" tab="用例">
        <a-button type="primary" @click="showCaseModal = true" style="margin-bottom: 16px">
          添加用例
        </a-button>
        <a-list :data-source="cases" row-key="id">
          <template #renderItem="{ item }">
            <a-list-item>
              <a-list-item-meta
                :title="item.name"
                :description="item.type"
              />
            </a-list-item>
          </template>
        </a-list>
      </a-tab-pane>

      <a-tab-pane key="scripts" tab="脚本">
        <a-upload
          :custom-request="handleUpload"
          accept=".py"
          style="margin-bottom: 16px"
          :show-upload-list="false"
        >
          <a-button :loading="uploading">上传脚本</a-button>
        </a-upload>
        <a-list :data-source="scripts" row-key="id">
          <template #renderItem="{ item }">
            <a-list-item>
              <a-list-item-meta
                :title="item.name"
                :description="item.file_path"
              />
            </a-list-item>
          </template>
        </a-list>
      </a-tab-pane>
    </a-tabs>

    <!-- 添加页面 Modal -->
    <a-modal v-model:open="showPageModal" title="添加页面" @ok="handleCreatePage">
      <a-form :model="pageForm" layout="vertical">
        <a-form-item label="页面名称" required>
          <a-input v-model:value="pageForm.name" />
        </a-form-item>
        <a-form-item label="描述">
          <a-input v-model:value="pageForm.description" />
        </a-form-item>
        <a-form-item label="所属项目">
          <a-input v-model:value="project?.name" disabled />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 添加用例 Modal -->
    <a-modal v-model:open="showCaseModal" title="添加用例" @ok="handleCreateCase">
      <a-form :model="caseForm" layout="vertical">
        <a-form-item label="用例名称" required>
          <a-input v-model:value="caseForm.name" />
        </a-form-item>
        <a-form-item label="类型">
          <a-select v-model:value="caseForm.type" disabled>
            <a-select-option value="keyword">关键字驱动</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="描述">
          <a-input v-model:value="caseForm.description" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  getProject, getPages, getCases, getScripts,
  uploadScript, createPage, createCase,
} from '../api'

const route = useRoute()
const router = useRouter()
const projectId = route.params.id

const project = ref(null)
const pages = ref([])
const cases = ref([])
const scripts = ref([])
const loading = ref(false)
const activeKey = ref('pages')
const showPageModal = ref(false)
const showCaseModal = ref(false)
const uploading = ref(false)

const pageForm = ref({ name: '', description: '' })
const caseForm = ref({ name: '', type: 'keyword', description: '' })

const fetchData = async () => {
  loading.value = true
  try {
    const [projectRes, pagesRes, casesRes, scriptsRes] = await Promise.all([
      getProject(projectId),
      getPages(projectId),
      getCases(projectId),
      getScripts(projectId),
    ])
    project.value = projectRes.data
    pages.value = pagesRes.data
    cases.value = casesRes.data
    scripts.value = scriptsRes.data
  } catch (error) {
    console.error('Failed to fetch project data:', error)
  } finally {
    loading.value = false
  }
}

const handleUpload = async ({ file }) => {
  uploading.value = true
  try {
    await uploadScript(projectId, file)
    message.success('脚本上传成功')
    fetchData()
  } catch (error) {
    message.error('脚本上传失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    uploading.value = false
  }
}

const handleCreatePage = async () => {
  if (!pageForm.value.name) return
  try {
    await createPage(projectId, pageForm.value)
    showPageModal.value = false
    pageForm.value = { name: '', description: '' }
    fetchData()
  } catch (error) {
    message.error('添加页面失败: ' + (error.response?.data?.detail || error.message))
  }
}

const handleCreateCase = async () => {
  if (!caseForm.value.name) return
  try {
    await createCase(projectId, caseForm.value)
    showCaseModal.value = false
    caseForm.value = { name: '', type: 'keyword', description: '' }
    fetchData()
  } catch (error) {
    message.error('添加用例失败: ' + (error.response?.data?.detail || error.message))
  }
}

const goBack = () => {
  router.push('/projects')
}

onMounted(fetchData)
</script>

<style scoped>
.project-detail {
  padding: 24px;
}
</style>
```

- [ ] **Step 2: 启动前端验证**

```bash
cd frontend && npm run dev
```

浏览器进入任意项目详情页，验证：
- "页面"tab 下"添加页面"按钮点击弹出 Modal，含页面名称、描述、所属项目（只读）
- "用例"tab 下"添加用例"按钮点击弹出 Modal，含用例名称、类型（仅"关键字驱动"）、描述
- "脚本"tab 下上传 `.py` 文件，成功时弹出 `message.success`，失败时弹出 `message.error`

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/ProjectDetail.vue
git commit -m "feat: add page/case modals and script upload feedback in project detail"
```

---

### Task 5: POManagement.vue 弹窗内显示项目名

**Files:**
- Modify: `frontend/src/views/POManagement.vue`

- [ ] **Step 1: 在创建 Page Object 弹窗中显示所属项目**

找到弹窗的 `<a-form>` 部分（约第 24-33 行），在描述字段后新增：

```vue
        <a-form-item label="所属项目">
          <span style="color: #666">{{ selectedProjectName }}</span>
        </a-form-item>
```

在 `<script setup>` 中新增 `computed` 导入和计算属性：

```javascript
import { ref, onMounted, h, computed } from 'vue'

const selectedProjectName = computed(() => {
  const p = projects.value.find(p => p.id === selectedProject.value)
  return p ? p.name : ''
})
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/POManagement.vue
git commit -m "feat: show project name in PO creation modal"
```

---

### Task 6: APKManagement.vue loading 修复 + 错误处理

**Files:**
- Modify: `backend/schemas/apk_package.py`
- Modify: `frontend/src/views/APKManagement.vue`

- [ ] **Step 1: 确保后端 datetime 序列化正确**

检查 `backend/schemas/apk_package.py` 已有 `model_config = ConfigDict(from_attributes=True)`，`uploaded_at: datetime` 应已被 Pydantic v2 自动序列化为 ISO 字符串。无需修改。若后续仍有 loading 问题，检查前端。

- [ ] **Step 2: 前端增加错误处理**

修改 `frontend/src/views/APKManagement.vue` 的 `fetchData` 方法：

```javascript
import { message } from 'ant-design-vue'

const fetchData = async () => {
  if (!selectedProject.value) return
  loading.value = true
  try {
    const res = await getApks(selectedProject.value)
    apks.value = res.data
  } catch (error) {
    message.error('获取APK列表失败: ' + (error.response?.data?.detail || error.message))
    apks.value = []
  } finally {
    loading.value = false
  }
}
```

同时确保 `handleUpload` 中也有错误提示：

```javascript
const handleUpload = async () => {
  if (!apkFile.value) return
  uploading.value = true
  try {
    await uploadApk(selectedProject.value, apkFile.value, uploadForm.value.version, uploadForm.value.description)
    message.success('APK 上传成功')
    showUploadModal.value = false
    apkFile.value = null
    fileList.value = []
    uploadForm.value = { version: '', description: '' }
    fetchData()
  } catch (error) {
    message.error('APK 上传失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    uploading.value = false
  }
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/APKManagement.vue
git commit -m "fix: APK list error handling and prevent stuck loading state"
```

---

### Task 7: TestCaseManagement.vue 关键字加载修复 + 去掉脚本驱动

**Files:**
- Modify: `frontend/src/views/TestCaseManagement.vue`

- [ ] **Step 1: 修复关键字分类提取**

当前 `kwCategories.value = catRes.data` 直接赋值为 API 返回的 `[{category, count}]`。需提取 `.category`：

```javascript
    kwCategories.value = catRes.data.map(c => c.category)
```

- [ ] **Step 2: 去掉"脚本驱动"选项**

找到类型选择 `<a-select>`（约第 62-66 行），删除脚本驱动选项：

```vue
            <a-select v-model:value="caseForm.type" disabled>
              <a-select-option value="keyword">关键字驱动</a-select-option>
            </a-select>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/TestCaseManagement.vue
git commit -m "fix: extract keyword categories correctly and remove script-driven type option"
```

---

### Task 8: ScriptManagement.vue 上传反馈

**Files:**
- Modify: `frontend/src/views/ScriptManagement.vue`

- [ ] **Step 1: 添加上传 loading 和消息提示**

修改 `<script setup>`，添加 `uploading` ref 和 `message` 导入：

```javascript
import { ref, onMounted, h } from 'vue'
import { message } from 'ant-design-vue'

const uploading = ref(false)

const handleUpload = async ({ file }) => {
  uploading.value = true
  try {
    await uploadScript(selectedProject.value, file)
    message.success('脚本上传成功')
    fetchData()
  } catch (error) {
    message.error('脚本上传失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    uploading.value = false
  }
}
```

修改上传按钮增加 loading：

```vue
    <a-upload v-if="selectedProject" :custom-request="handleUpload" accept=".py" style="margin-top: 16px" :show-upload-list="false">
      <a-button type="primary" :loading="uploading">上传脚本</a-button>
    </a-upload>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/ScriptManagement.vue
git commit -m "feat: add upload loading and message feedback for script management"
```

---

### Task 9: Devices.vue 简化 + 中文化

**Files:**
- Modify: `backend/api/devices.py`
- Modify: `frontend/src/views/Devices.vue`
- Modify: `frontend/src/api/index.js`

- [ ] **Step 1: 后端新增一键连接 API**

在 `backend/api/devices.py` 末尾新增：

```python
@router.post("/devices/{serial}/connect")
def connect_device_one_click(serial: str):
    """一键连接 USB 设备：先 adb tcpip 开放端口，再 adb connect。"""
    # 1. 切换到 tcpip 模式
    tcpip_result = DeviceScanner.tcpip_device(serial, 5555)
    if not tcpip_result["success"]:
        raise HTTPException(status_code=400, detail=tcpip_result["message"])

    # 2. 获取设备 IP
    import time
    time.sleep(1)
    devices = DeviceScanner.scan_devices()
    device_info = devices.get(serial, {})
    ip = ""
    # 尝试从设备信息中获取 IP
    for key, value in device_info.items():
        if value and ":" not in value and "." in value:
            # 可能是 IP 地址
            parts = value.split(".")
            if len(parts) == 4 and all(p.isdigit() for p in parts):
                ip = value
                break

    if not ip:
        # 从 adb shell 获取 IP
        try:
            result = subprocess.run(
                [settings.adb_path, "-s", serial, "shell", "ip", "route"],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.split("\n"):
                if "src" in line:
                    parts = line.split()
                    if "src" in parts:
                        idx = parts.index("src")
                        if idx + 1 < len(parts):
                            ip = parts[idx + 1]
                            break
        except Exception:
            pass

    if not ip:
        raise HTTPException(status_code=400, detail="无法获取设备 IP 地址")

    # 3. 连接
    connect_result = DeviceScanner.connect_device(ip, 5555)
    if not connect_result["success"]:
        raise HTTPException(status_code=400, detail=connect_result["message"])

    # 4. 同步设备列表
    db = SessionLocal()
    DeviceScanner.sync_devices(db)
    db.close()

    return {"success": True, "message": f"已连接 {ip}:5555", "serial": f"{ip}:5555"}
```

注意需要确保 `import subprocess` 在文件顶部。

- [ ] **Step 2: 前端修改 Devices.vue**

替换整个 `frontend/src/views/Devices.vue`：

```vue
<template>
  <div class="devices">
    <a-page-header title="设备管理" sub-title="管理测试设备">
      <template #extra>
        <a-button @click="handleScan" :loading="scanning">扫描设备</a-button>
      </template>
    </a-page-header>

    <a-table :columns="columns" :data-source="devices" :loading="loading" row-key="id" style="margin-top: 16px">
      <template #status="{ record }">
        <a-tag :color="record.status === 'online' ? 'green' : 'red'">{{ record.status }}</a-tag>
      </template>
      <template #connType="{ record }">
        <a-tag :color="isTcpipDevice(record.serial) ? 'blue' : 'default'">
          {{ isTcpipDevice(record.serial) ? 'TCP/IP' : 'USB' }}
        </a-tag>
      </template>
      <template #action="{ record }">
        <a-button v-if="isTcpipDevice(record.serial)" type="link" danger @click="handleDisconnect(record)">断开</a-button>
        <a-button v-else type="link" @click="handleConnect(record)">连接</a-button>
      </template>
    </a-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { getDevices, scanDevices, disconnectDevice, connectDeviceOneClick } from '../api'

const devices = ref([])
const loading = ref(false)
const scanning = ref(false)

const isTcpipDevice = (serial) => {
  return serial && serial.includes(':')
}

const columns = [
  { title: '名称', dataIndex: 'name', key: 'name' },
  { title: '序列号', dataIndex: 'serial', key: 'serial' },
  { title: '平台', dataIndex: 'platform', key: 'platform' },
  { title: '连接方式', key: 'connType', slots: { customRender: 'connType' } },
  { title: '状态', dataIndex: 'status', key: 'status', slots: { customRender: 'status' } },
  { title: '操作', key: 'action', slots: { customRender: 'action' } },
]

const fetchDevices = async () => {
  loading.value = true
  try {
    const res = await getDevices()
    devices.value = res.data
  } catch (error) {
    message.error('获取设备列表失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

const handleScan = async () => {
  scanning.value = true
  try {
    await scanDevices()
    await fetchDevices()
  } catch (error) {
    message.error('扫描设备失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    scanning.value = false
  }
}

const handleConnect = async (device) => {
  try {
    const res = await connectDeviceOneClick(device.serial)
    message.success(res.data.message)
    setTimeout(() => fetchDevices(), 2000)
  } catch (error) {
    message.error('连接失败: ' + (error.response?.data?.detail || error.message))
  }
}

const handleDisconnect = async (device) => {
  try {
    const parts = device.serial.split(':')
    await disconnectDevice(parts[0], parseInt(parts[1]) || 5555)
    message.success('已断开连接')
    setTimeout(() => fetchDevices(), 1000)
  } catch (error) {
    message.error('断开连接失败: ' + (error.response?.data?.detail || error.message))
  }
}

onMounted(fetchDevices)
</script>

<style scoped>
.devices { padding: 24px; }
</style>
```

- [ ] **Step 3: 前端 API 层添加新方法**

在 `frontend/src/api/index.js` 末尾添加：

```javascript
// Device one-click connect
export const connectDeviceOneClick = (serial) => api.post(`/api/devices/${serial}/connect`)
```

- [ ] **Step 4: Commit**

```bash
git add backend/api/devices.py frontend/src/views/Devices.vue frontend/src/api/index.js
git commit -m "feat: simplify device management, add one-click connect, remove TCP/IP modal"
```

---

### Task 10: Tasks.vue 中文化 + 准备脚本支持（前端框架）

**Files:**
- Modify: `frontend/src/views/Tasks.vue`

- [ ] **Step 1: 中文化 + 增加 script_id 字段结构**

此任务仅做前端中文化和字段准备，`script_id` 的真实支持在 Task 14 完成。

替换 `frontend/src/views/Tasks.vue`：

```vue
<template>
  <div class="tasks">
    <a-page-header title="任务管理" sub-title="执行测试任务">
      <template #extra>
        <a-button type="primary" @click="openCreateModal">创建任务</a-button>
      </template>
    </a-page-header>

    <a-table :columns="columns" :data-source="tasks" :loading="loading" row-key="id" style="margin-top: 16px">
      <template #contentName="{ record }">{{ getContentName(record) }}</template>
      <template #contentType="{ record }">
        <a-tag :color="record.case_id ? 'blue' : 'orange'">{{ record.case_id ? '用例' : '脚本' }}</a-tag>
      </template>
      <template #apkVersion="{ record }">{{ getApkLabel(record.apk_id) }}</template>
      <template #status="{ record }">
        <a-tag :color="getStatusColor(record.status)">{{ record.status }}</a-tag>
      </template>
      <template #action="{ record }">
        <a-button v-if="record.status === 'pending'" type="link" @click="handleExecute(record.id)">执行</a-button>
        <span v-else style="color: #999">{{ record.status }}</span>
      </template>
    </a-table>

    <!-- 创建任务弹窗 -->
    <a-modal v-model:open="showCreateModal" title="创建任务" @ok="handleCreateTask" :confirm-loading="creating">
      <a-form :model="taskForm" layout="vertical">
        <a-form-item label="项目" required>
          <a-select v-model:value="taskForm.projectId" placeholder="选择项目" @change="onProjectChange">
            <a-select-option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="测试内容" required>
          <a-select v-model:value="taskForm.content_id" placeholder="选择用例或脚本">
            <a-select-opt-group label="用例">
              <a-select-option v-for="c in projectCases" :key="`case-${c.id}`" :value="`case-${c.id}`">{{ c.name }}</a-select-option>
            </a-select-opt-group>
            <a-select-opt-group label="脚本">
              <a-select-option v-for="s in projectScripts" :key="`script-${s.id}`" :value="`script-${s.id}`">{{ s.name }}</a-select-option>
            </a-select-opt-group>
          </a-select>
        </a-form-item>
        <a-form-item label="APK版本">
          <a-select v-model:value="taskForm.apk_id" placeholder="选择APK版本" allowClear>
            <a-select-option :value="null">不安装APK</a-select-option>
            <a-select-option v-for="apk in projectApks" :key="apk.id" :value="apk.id">
              {{ apk.version }} ({{ apk.package_name || '未知包名' }})
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="目标设备" required>
          <a-checkbox-group v-model:value="taskForm.device_ids">
            <a-checkbox v-for="d in onlineDevices" :key="d.id" :value="d.id">
              {{ d.name || d.serial }} <a-tag :color="d.status === 'online' ? 'green' : 'red'" size="small">{{ d.status }}</a-tag>
            </a-checkbox>
          </a-checkbox-group>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  getProjects, getCases, getScripts, getApks, getDevices, getTasks,
  createTask, executeTask as executeTaskApi,
} from '../api'

const tasks = ref([])
const projects = ref([])
const projectCases = ref([])
const projectScripts = ref([])
const projectApks = ref([])
const devices = ref([])
const loading = ref(false)
const creating = ref(false)
const showCreateModal = ref(false)

const taskForm = ref({
  projectId: null,
  content_id: null,
  apk_id: null,
  device_ids: [],
})

const onlineDevices = computed(() => devices.value.filter(d => d.status === 'online'))

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 120 },
  { title: '测试内容', key: 'contentName', slots: { customRender: 'contentName' } },
  { title: '类型', key: 'contentType', slots: { customRender: 'contentType' } },
  { title: 'APK版本', key: 'apkVersion', slots: { customRender: 'apkVersion' } },
  { title: '状态', dataIndex: 'status', key: 'status', slots: { customRender: 'status' } },
  { title: '创建时间', dataIndex: 'created_at', key: 'created_at' },
  { title: '操作', key: 'action', slots: { customRender: 'action' } },
]

const getStatusColor = (status) => {
  const colors = { pending: 'default', running: 'blue', completed: 'green', failed: 'red', skipped: 'orange' }
  return colors[status] || 'default'
}

const getContentName = (record) => {
  if (record.case_id) {
    const c = projectCases.value.find(c => c.id === record.case_id)
    return c ? c.name : record.case_id
  }
  if (record.script_id) {
    const s = projectScripts.value.find(s => s.id === record.script_id)
    return s ? s.name : record.script_id
  }
  return '-'
}

const getApkLabel = (apkId) => {
  if (!apkId) return '不安装'
  const apk = projectApks.value.find(a => a.id === apkId)
  return apk ? `${apk.version}` : apkId
}

const fetchTasks = async () => {
  loading.value = true
  try {
    const res = await getTasks()
    tasks.value = res.data
  } catch (error) {
    console.error('Failed to fetch tasks:', error)
  } finally {
    loading.value = false
  }
}

const openCreateModal = async () => {
  taskForm.value = { projectId: null, content_id: null, apk_id: null, device_ids: [] }
  showCreateModal.value = true
  try {
    const [projRes, devRes] = await Promise.all([getProjects(), getDevices()])
    projects.value = projRes.data
    devices.value = devRes.data
  } catch (error) {
    console.error('Failed to load modal data:', error)
  }
}

const onProjectChange = async (projectId) => {
  taskForm.value.content_id = null
  taskForm.value.apk_id = null
  try {
    const [caseRes, scriptRes, apkRes] = await Promise.all([
      getCases(projectId),
      getScripts(projectId),
      getApks(projectId),
    ])
    projectCases.value = caseRes.data
    projectScripts.value = scriptRes.data
    projectApks.value = apkRes.data
  } catch (error) {
    console.error('Failed to load project data:', error)
  }
}

const handleCreateTask = async () => {
  if (!taskForm.value.content_id || taskForm.value.device_ids.length === 0) {
    alert('请选择测试内容和至少一个设备')
    return
  }
  creating.value = true
  try {
    const payload = {
      apk_id: taskForm.value.apk_id,
      device_ids: taskForm.value.device_ids,
    }
    if (taskForm.value.content_id.startsWith('case-')) {
      payload.case_id = taskForm.value.content_id.replace('case-', '')
    } else if (taskForm.value.content_id.startsWith('script-')) {
      payload.script_id = taskForm.value.content_id.replace('script-', '')
    }
    await createTask(payload)
    showCreateModal.value = false
    fetchTasks()
  } catch (error) {
    console.error('Failed to create task:', error)
    alert('创建失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    creating.value = false
  }
}

const handleExecute = async (id) => {
  try {
    await executeTaskApi(id)
    fetchTasks()
  } catch (error) {
    console.error('Failed to execute task:', error)
  }
}

onMounted(fetchTasks)
</script>

<style scoped>
.tasks { padding: 24px; }
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/Tasks.vue
git commit -m "feat: localize Tasks page and prepare grouped case/script selection UI"
```

---

### Task 11: Keywords.vue 中文化 + 准备自定义关键字（前端框架）

**Files:**
- Modify: `frontend/src/views/Keywords.vue`

- [ ] **Step 1: 中文化 + 增加创建/编辑/删除结构**

替换整个 `frontend/src/views/Keywords.vue`：

```vue
<template>
  <div class="keywords">
    <a-page-header
      title="关键字管理"
      sub-title="内置关键字和自定义关键字"
    >
      <template #extra>
        <a-button type="primary" @click="openCreateModal">创建自定义关键字</a-button>
      </template>
    </a-page-header>

    <a-table
      :columns="columns"
      :data-source="keywords"
      :loading="loading"
      row-key="id"
      style="margin-top: 24px"
    >
      <template #category="{ record }">
        <a-tag :color="getCategoryColor(record.category)">
          {{ record.category }}
        </a-tag>
      </template>
      <template #action="{ record }">
        <a-button v-if="record.category === 'custom'" type="link" @click="openEditModal(record)">编辑</a-button>
        <a-popconfirm v-if="record.category === 'custom'" title="确定删除?" @confirm="handleDelete(record.id)">
          <a-button type="link" danger>删除</a-button>
        </a-popconfirm>
      </template>
    </a-table>

    <!-- 创建/编辑弹窗 -->
    <a-modal
      v-model:open="showModal"
      :title="isEditing ? '编辑自定义关键字' : '创建自定义关键字'"
      @ok="handleSave"
      :confirm-loading="saving"
      width="700"
    >
      <a-form :model="form" layout="vertical">
        <a-form-item label="关键字名称" required>
          <a-input v-model:value="form.name" :disabled="isEditing" />
        </a-form-item>
        <a-form-item label="描述" required>
          <a-input v-model:value="form.description" />
        </a-form-item>
        <a-form-item label="平台">
          <a-select v-model:value="form.platform">
            <a-select-option value="all">全部</a-select-option>
            <a-select-option value="android">Android</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="Python 代码">
          <a-textarea v-model:value="form.code" :rows="8" placeholder="def your_keyword(d, locator, params): ..." />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { getKeywords, createCustomKeyword, updateKeyword, deleteKeyword } from '../api'

const keywords = ref([])
const loading = ref(false)
const showModal = ref(false)
const saving = ref(false)
const isEditing = ref(false)
const editingId = ref(null)

const form = ref({
  name: '',
  description: '',
  platform: 'all',
  code: '',
})

const columns = [
  { title: '关键字名称', dataIndex: 'name', key: 'name' },
  { title: '分类', dataIndex: 'category', key: 'category', slots: { customRender: 'category' } },
  { title: '平台', dataIndex: 'platform', key: 'platform' },
  { title: '描述', dataIndex: 'description', key: 'description' },
  { title: '操作', key: 'action', slots: { customRender: 'action' } },
]

const getCategoryColor = (category) => {
  const colors = {
    basic: 'green',
    platform: 'blue',
    custom: 'orange',
  }
  return colors[category] || 'default'
}

const fetchKeywords = async () => {
  loading.value = true
  try {
    const res = await getKeywords()
    keywords.value = res.data
  } catch (error) {
    message.error('获取关键字失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

const openCreateModal = () => {
  isEditing.value = false
  editingId.value = null
  form.value = { name: '', description: '', platform: 'all', code: '' }
  showModal.value = true
}

const openEditModal = (record) => {
  isEditing.value = true
  editingId.value = record.id
  form.value = {
    name: record.name,
    description: record.description || '',
    platform: record.platform || 'all',
    code: record.code || '',
  }
  showModal.value = true
}

const handleSave = async () => {
  if (!form.value.name || !form.value.description) {
    message.warning('请填写必填项')
    return
  }
  saving.value = true
  try {
    if (isEditing.value) {
      await updateKeyword(editingId.value, form.value)
      message.success('关键字更新成功')
    } else {
      await createCustomKeyword('default', form.value)
      message.success('关键字创建成功')
    }
    showModal.value = false
    fetchKeywords()
  } catch (error) {
    message.error('保存失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    saving.value = false
  }
}

const handleDelete = async (id) => {
  try {
    await deleteKeyword(id)
    message.success('关键字删除成功')
    fetchKeywords()
  } catch (error) {
    message.error('删除失败: ' + (error.response?.data?.detail || error.message))
  }
}

onMounted(fetchKeywords)
</script>

<style scoped>
.keywords {
  padding: 24px;
}
</style>
```

- [ ] **Step 2: 前端 API 层添加新方法**

在 `frontend/src/api/index.js` 末尾添加：

```javascript
// Keywords CRUD
export const updateKeyword = (id, data) => api.put(`/api/keywords/${id}`, data)
export const deleteKeyword = (id) => api.delete(`/api/keywords/${id}`)
```

修改现有的 `createCustomKeyword`：

```javascript
export const createCustomKeyword = (projectId, data) => api.post(`/api/projects/${projectId}/custom-keywords`, data)
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/Keywords.vue frontend/src/api/index.js
git commit -m "feat: localize Keywords page and add custom keyword CRUD UI"
```

---

### Task 12: Debug.vue 中文化 + iframe 错误提示

**Files:**
- Modify: `frontend/src/views/Debug.vue`

- [ ] **Step 1: 中文化 + iframe 错误处理**

替换整个 `frontend/src/views/Debug.vue`：

```vue
<template>
  <div class="debug">
    <a-page-header
      title="调试"
      sub-title="使用 uiautodev 调试设备"
    />

    <a-row :gutter="[16, 16]" style="margin-top: 24px">
      <a-col :span="24">
        <a-card title="uiautodev 状态">
          <a-descriptions :column="2">
            <a-descriptions-item label="状态">
              <a-tag :color="uiautodevStatus.running ? 'green' : 'red'">
                {{ uiautodevStatus.running ? '运行中' : '已停止' }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="URL">
              <a :href="uiautodevStatus.url" target="_blank">{{ uiautodevStatus.url }}</a>
            </a-descriptions-item>
            <a-descriptions-item label="主机">{{ uiautodevStatus.host }}</a-descriptions-item>
            <a-descriptions-item label="端口">{{ uiautodevStatus.port }}</a-descriptions-item>
          </a-descriptions>
          <a-space>
            <a-button type="primary" @click="startUiautodev">启动</a-button>
            <a-button danger @click="stopUiautodev">停止</a-button>
          </a-space>
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="[16, 16]" style="margin-top: 24px">
      <a-col :span="24">
        <a-card title="设备检查器">
          <a-select
            v-model:value="selectedDevice"
            placeholder="选择设备"
            style="width: 300px; margin-bottom: 16px"
            @change="handleDeviceChange"
          >
            <a-select-option v-for="device in devices" :key="device.id" :value="device.serial">
              {{ device.name || device.serial }}
            </a-select-option>
          </a-select>
          <div v-if="selectedDevice">
            <a-alert v-if="iframeError" :message="iframeError" type="error" show-icon style="margin-bottom: 12px" />
            <div v-if="!uiautodevStatus.running" class="iframe-container">
              <a-alert message="uiautodev 未运行，请先启动" type="warning" />
            </div>
            <div v-else class="iframe-container">
              <iframe
                :src="iframeUrl"
                width="100%"
                height="800"
                frameborder="0"
                @error="iframeError = 'iframe 加载失败'"
              />
            </div>
          </div>
          <a-empty v-else description="请选择设备开始调试" />
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { getDevices } from '../api'

const devices = ref([])
const selectedDevice = ref(null)
const iframeUrl = ref('')
const iframeError = ref('')
const uiautodevStatus = ref({
  running: false,
  url: '',
  host: '',
  port: 0,
})

const fetchDevices = async () => {
  try {
    const res = await getDevices()
    devices.value = res.data
  } catch (error) {
    console.error('Failed to fetch devices:', error)
  }
}

const fetchUiautodevStatus = async () => {
  try {
    const res = await axios.get('/api/debug/uiautodev/status')
    uiautodevStatus.value = res.data
  } catch (error) {
    console.error('Failed to fetch uiautodev status:', error)
  }
}

const startUiautodev = async () => {
  try {
    await axios.post('/api/debug/uiautodev/start')
    await fetchUiautodevStatus()
  } catch (error) {
    console.error('Failed to start uiautodev:', error)
  }
}

const stopUiautodev = async () => {
  try {
    await axios.post('/api/debug/uiautodev/stop')
    await fetchUiautodevStatus()
  } catch (error) {
    console.error('Failed to stop uiautodev:', error)
  }
}

const handleDeviceChange = async (serial) => {
  iframeError.value = ''
  try {
    const res = await axios.get(`/api/debug/uiautodev/device/${serial}`)
    iframeUrl.value = res.data.url
  } catch (error) {
    iframeError.value = '获取设备调试 URL 失败: ' + (error.response?.data?.detail || error.message)
  }
}

onMounted(() => {
  fetchDevices()
  fetchUiautodevStatus()
})
</script>

<style scoped>
.debug {
  padding: 24px;
}

.iframe-container {
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  overflow: hidden;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/Debug.vue
git commit -m "feat: localize Debug page and add iframe error handling"
```

---

## Phase 2: Bug 修复

### Task 13: 删除项目二次确认（后端 stats + 前端接入）

**Files:**
- Modify: `backend/api/projects.py`
- Modify: `frontend/src/views/Projects.vue`
- Modify: `frontend/src/api/index.js`
- Test: `backend/tests/test_projects.py`

- [ ] **Step 1: 编写项目 stats 接口测试**

在 `backend/tests/test_projects.py` 末尾添加：

```python
def test_get_project_stats():
    # 先创建一个项目
    response = client.post("/api/projects", json={"name": "StatsTest", "platform": "android"})
    assert response.status_code == 200
    project_id = response.json()["id"]

    response = client.get(f"/api/projects/{project_id}/stats")
    assert response.status_code == 200
    data = response.json()
    assert "pages" in data
    assert "cases" in data
    assert "scripts" in data
    assert isinstance(data["pages"], int)
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd backend && pytest tests/test_projects.py::test_get_project_stats -v
```

Expected: `FAIL` — `404 Not Found`

- [ ] **Step 3: 实现项目 stats 接口**

在 `backend/api/projects.py` 的 `delete_project` 函数前添加：

```python
from models.page_object import PageObject
from models.test_case import TestCase
from models.script import Script


@router.get("/{project_id}/stats")
def get_project_stats(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    page_count = db.query(PageObject).filter(PageObject.project_id == project_id).count()
    case_count = db.query(TestCase).filter(TestCase.project_id == project_id).count()
    script_count = db.query(Script).filter(Script.project_id == project_id).count()
    return {
        "pages": page_count,
        "cases": case_count,
        "scripts": script_count,
    }
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd backend && pytest tests/test_projects.py::test_get_project_stats -v
```

Expected: `PASS`

- [ ] **Step 5: 前端接入 stats API**

在 `frontend/src/api/index.js` 添加：

```javascript
export const getProjectStats = (id) => api.get(`/api/projects/${id}/stats`)
```

修改 `frontend/src/views/Projects.vue` 的 `onDeleteClick`：

```javascript
import { getProjectStats } from '../api'

const onDeleteClick = async (record) => {
  pendingDeleteId.value = record.id
  try {
    const res = await getProjectStats(record.id)
    const stats = res.data
    const total = stats.pages + stats.cases + stats.scripts
    if (total > 0) {
      pendingDeleteHasData.value = true
      deleteModalTitle.value = '无法删除'
      deleteModalContent.value = `该项目下存在 ${stats.pages} 个页面、${stats.cases} 个用例、${stats.scripts} 个脚本，请先清除所有关联数据后再删除。`
      deleteOkProps.value = { style: { display: 'none' } }
    } else {
      pendingDeleteHasData.value = false
      deleteModalTitle.value = '确认删除'
      deleteModalContent.value = `确定删除项目「${record.name}」吗？删除后不可恢复。`
      deleteOkProps.value = { danger: true }
    }
    showDeleteModal.value = true
  } catch (error) {
    message.error('获取项目统计失败: ' + (error.response?.data?.detail || error.message))
  }
}
```

同时确保导入了 `message`：

```javascript
import { message } from 'ant-design-vue'
```

- [ ] **Step 6: Commit**

```bash
git add backend/api/projects.py backend/tests/test_projects.py frontend/src/views/Projects.vue frontend/src/api/index.js
git commit -m "feat: add project stats API and block deletion when data exists"
```

---

### Task 14: 后端支持 script_id（模型 + Schema + API + 任务调度）

**Files:**
- Modify: `backend/models/test_task.py`
- Modify: `backend/schemas/test_task.py`
- Modify: `backend/api/tasks.py`
- Modify: `backend/core/task_dispatcher.py`
- Modify: `backend/executors/script_executor.py`
- Test: `backend/tests/test_tasks_script.py`

- [ ] **Step 1: 修改模型和 schema**

修改 `backend/models/test_task.py`：

```python
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from models.base import Base


def utc_now():
    return datetime.now(timezone.utc)


class TestTask(Base):
    __tablename__ = "test_tasks"
    id = Column(String, primary_key=True, default=lambda: f"task_{uuid.uuid4().hex[:8]}")
    case_id = Column(String, ForeignKey("test_cases.id"), nullable=True)
    script_id = Column(String, ForeignKey("scripts.id"), nullable=True)
    apk_id = Column(String, ForeignKey("apk_packages.id"), nullable=True)
    device_ids = Column(Text, nullable=False)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=utc_now)
    results = relationship("TaskResult", back_populates="test_task", cascade="all, delete-orphan")
```

修改 `backend/schemas/test_task.py`：

```python
from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime

class TaskResultBase(BaseModel):
    device_id: str
    status: str = "pending"
    start_time: datetime | None = None
    end_time: datetime | None = None
    log_path: str | None = None
    report_path: str | None = None

class TaskResultResponse(TaskResultBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    task_id: str

class TestTaskBase(BaseModel):
    case_id: str | None = None
    script_id: str | None = None
    apk_id: str | None = None
    device_ids: list[str]
    status: str = "pending"

class TestTaskCreate(TestTaskBase):
    @field_validator("case_id")
    @classmethod
    def validate_case_or_script(cls, v, info):
        data = info.data
        if not v and not data.get("script_id"):
            raise ValueError("case_id 或 script_id 必须提供一个")
        if v and data.get("script_id"):
            raise ValueError("case_id 和 script_id 不能同时提供")
        return v

class TestTaskUpdate(BaseModel):
    status: str | None = None

class TestTaskResponse(TestTaskBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime
    results: list[TaskResultResponse] = []
```

- [ ] **Step 2: 修改 tasks API**

替换 `backend/api/tasks.py` 的 `create_task` 函数：

```python
@router.post("/tasks", response_model=TestTaskResponse)
def create_task(task: TestTaskCreate, db: Session = Depends(get_db)):
    db_task = TestTask(
        case_id=task.case_id,
        script_id=task.script_id,
        apk_id=task.apk_id,
        device_ids=json.dumps(task.device_ids),
        status="pending",
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    for device_id in task.device_ids:
        result = TaskResult(task_id=db_task.id, device_id=device_id, status="pending")
        db.add(result)
    db.commit()
    db.refresh(db_task)

    if isinstance(db_task.device_ids, str):
        db_task.device_ids = json.loads(db_task.device_ids)
    return db_task
```

- [ ] **Step 3: 修改任务调度器**

替换 `backend/core/task_dispatcher.py` 的 `dispatch` 方法：

```python
    def dispatch(self, task_id: str, db: Session = None) -> Dict:
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False

        try:
            task = db.query(TestTask).filter(TestTask.id == task_id).first()
            if not task:
                return {"status": "failed", "error": "Task not found"}

            test_case = None
            script = None
            if task.case_id:
                test_case = db.query(TestCase).filter(TestCase.id == task.case_id).first()
                if not test_case:
                    return {"status": "failed", "error": "Test case not found"}
                project = db.query(Project).filter(Project.id == test_case.project_id).first()
            elif task.script_id:
                script = db.query(Script).filter(Script.id == task.script_id).first()
                if not script:
                    return {"status": "failed", "error": "Script not found"}
                project = db.query(Project).filter(Project.id == script.project_id).first()
            else:
                return {"status": "failed", "error": "No case_id or script_id specified"}

            device_ids = json.loads(task.device_ids)
            task.status = "running"
            db.commit()

            results = {}
            with ThreadPoolExecutor(max_workers=len(device_ids)) as executor:
                futures = {}
                for device_id in device_ids:
                    future = executor.submit(
                        self._execute_on_device,
                        task_id,
                        test_case,
                        script,
                        device_id,
                        project,
                        db
                    )
                    futures[future] = device_id

                for future in as_completed(futures):
                    device_id = futures[future]
                    try:
                        result = future.result()
                        results[device_id] = result
                    except Exception as e:
                        results[device_id] = {
                            "status": "failed",
                            "error": str(e),
                        }

            task.status = "completed"
            db.commit()

            return {
                "status": "completed",
                "task_id": task_id,
                "results": results,
            }

        finally:
            if should_close:
                db.close()

    def _execute_on_device(self, task_id: str, test_case: TestCase, script: Script,
                           device_id: str, project: Project, db: Session) -> Dict:
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            return {"status": "failed", "error": f"Device {device_id} not found"}

        result = db.query(TaskResult).filter(
            TaskResult.task_id == task_id,
            TaskResult.device_id == device_id
        ).first()

        if not result:
            result = TaskResult(task_id=task_id, device_id=device_id, status="running")
            db.add(result)
            db.commit()

        result.status = "running"
        result.start_time = datetime.now(timezone.utc)
        db.commit()

        try:
            if script:
                executor = self.executors["script"]
                execution_result = executor.run_script(script, device, project, db)
            else:
                if test_case.type == "script":
                    executor = self.executors["script"]
                else:
                    executor = self.executors["android"]
                execution_result = executor.run(test_case, device, project, db)

            result.status = execution_result.get("status", "failed")
            result.end_time = datetime.now(timezone.utc)
            db.commit()

            return execution_result

        except Exception as e:
            result.status = "failed"
            result.end_time = datetime.now(timezone.utc)
            db.commit()

            return {"status": "failed", "error": str(e)}
```

- [ ] **Step 4: ScriptExecutor 添加 run_script 方法**

在 `backend/executors/script_executor.py` 的 `ScriptExecutor` 类中添加：

```python
    def run_script(self, script, device, project=None, db=None):
        """Execute a script directly (without wrapper test case)."""
        result = {
            "status": "pending",
            "logs": [],
            "stdout": "",
            "stderr": "",
            "exit_code": None,
            "error": None,
        }

        try:
            script_path = script.file_path
            if not os.path.exists(script_path):
                result["status"] = "failed"
                result["error"] = f"Script file not found: {script_path}"
                return result

            env = os.environ.copy()
            env["DEVICE_SERIAL"] = device.serial
            if project and project.app_id:
                env["APP_PACKAGE"] = project.app_id

            self._log(f"Executing script: {script_path} on device {device.serial}")

            self.process = subprocess.Popen(
                ["python", script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                cwd=os.path.dirname(script_path),
            )

            stdout, stderr = self.process.communicate()
            result["stdout"] = stdout
            result["stderr"] = stderr
            result["exit_code"] = self.process.returncode

            if stdout:
                for line in stdout.strip().split("\n"):
                    self._log(line, "INFO")
            if stderr:
                for line in stderr.strip().split("\n"):
                    self._log(line, "ERROR")

            if self.process.returncode == 0:
                result["status"] = "success"
                self._log("Script executed successfully", "INFO")
            else:
                result["status"] = "failed"
                self._log(f"Script failed with exit code {self.process.returncode}", "ERROR")

            result["logs"] = self.logs

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            self._log(f"Script execution failed: {e}", "ERROR")

        return result
```

- [ ] **Step 5: 编写并运行测试**

创建 `backend/tests/test_tasks_script.py`：

```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_task_with_case():
    proj = client.post("/api/projects", json={"name": "ScriptTaskTest", "platform": "android"})
    project_id = proj.json()["id"]

    case = client.post(f"/api/projects/{project_id}/cases", json={
        "name": "TestCase",
        "type": "keyword",
        "steps": [],
    })
    case_id = case.json()["id"]

    response = client.post("/api/tasks", json={
        "case_id": case_id,
        "device_ids": ["device1"],
    })
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == case_id
    assert data["script_id"] is None

def test_create_task_without_case_or_script_fails():
    response = client.post("/api/tasks", json={
        "device_ids": ["device1"],
    })
    assert response.status_code == 422

def test_create_task_with_both_case_and_script_fails():
    response = client.post("/api/tasks", json={
        "case_id": "fake_case",
        "script_id": "fake_script",
        "device_ids": ["device1"],
    })
    assert response.status_code == 422
```

运行测试：

```bash
cd backend && pytest tests/test_tasks_script.py -v
```

Expected: `PASS`

- [ ] **Step 6: Commit**

```bash
git add backend/models/test_task.py backend/schemas/test_task.py backend/api/tasks.py backend/core/task_dispatcher.py backend/executors/script_executor.py backend/tests/test_tasks_script.py
git commit -m "feat: support script_id in tasks, update dispatcher and schema validation"
```

---

### Task 15: 后端支持自定义关键字（模型 + Schema + API + 加载器 + 执行器）

**Files:**
- Modify: `backend/models/keyword.py`
- Modify: `backend/schemas/keyword.py`
- Modify: `backend/api/keywords.py`
- Create: `backend/core/custom_keyword_loader.py`
- Modify: `backend/executors/android_executor.py`
- Modify: `backend/db/init_db.py`
- Test: `backend/tests/test_custom_keywords.py`

- [ ] **Step 1: 修改模型和 schema 增加 code 字段**

修改 `backend/models/keyword.py`：

```python
import uuid
from sqlalchemy import Column, String, Text
from models.base import Base


class Keyword(Base):
    __tablename__ = "keywords"
    id = Column(String, primary_key=True, default=lambda: f"kw_{uuid.uuid4().hex[:8]}")
    name = Column(String, nullable=False, unique=True)
    category = Column(String, nullable=False)
    platform = Column(String, default="all")
    params = Column(Text)
    description = Column(String)
    code = Column(Text)
```

修改 `backend/schemas/keyword.py`：

```python
from pydantic import BaseModel, ConfigDict

class KeywordBase(BaseModel):
    name: str
    category: str = "custom"
    platform: str = "all"
    params: str | None = None
    description: str | None = None
    code: str | None = None

class KeywordCreate(KeywordBase):
    pass

class KeywordResponse(KeywordBase):
    model_config = ConfigDict(from_attributes=True)
    id: str

class KeywordCategoryResponse(BaseModel):
    category: str
    count: int
```

- [ ] **Step 2: 创建自定义关键字加载器**

创建 `backend/core/custom_keyword_loader.py`：

```python
import ast
import os
import sys
import importlib.util
from pathlib import Path
from config import settings

CUSTOM_KEYWORDS_DIR = settings.scripts_dir / "custom_keywords"


def ensure_directory():
    os.makedirs(CUSTOM_KEYWORDS_DIR, exist_ok=True)
    init_file = CUSTOM_KEYWORDS_DIR / "__init__.py"
    if not init_file.exists():
        init_file.write_text("", encoding="utf-8")


def validate_code(code: str):
    """Validate Python code syntax using ast.parse."""
    try:
        ast.parse(code)
        return True, ""
    except SyntaxError as e:
        return False, f"Syntax error at line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, str(e)


def write_keyword_file(name: str, code: str):
    """Write custom keyword code to a Python module file."""
    ensure_directory()
    file_path = CUSTOM_KEYWORDS_DIR / f"{name}.py"
    file_path.write_text(code, encoding="utf-8")


def load_custom_keyword_function(name: str):
    """Dynamically load a custom keyword function."""
    ensure_directory()
    file_path = CUSTOM_KEYWORDS_DIR / f"{name}.py"
    if not file_path.exists():
        return None

    spec = importlib.util.spec_from_file_location(f"custom_keywords.{name}", str(file_path))
    if not spec or not spec.loader:
        return None

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    func = getattr(module, name, None)
    return func


def reload_custom_keywords():
    """Reload all custom keyword modules."""
    ensure_directory()
    to_remove = [key for key in sys.modules if key.startswith("custom_keywords.")]
    for key in to_remove:
        del sys.modules[key]
```

修改 `backend/db/init_db.py`，在 `init_db()` 函数开头添加：

```python
from core.custom_keyword_loader import ensure_directory

# ... existing imports ...

def init_db():
    Base.metadata.create_all(bind=engine)
    ensure_directory()  # 确保 custom_keywords 目录存在
    # ... rest of the function ...
```

- [ ] **Step 3: 修改 keywords API**

替换 `backend/api/keywords.py`：

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db
from models.keyword import Keyword
from schemas.keyword import KeywordCreate, KeywordResponse, KeywordCategoryResponse
from core.keyword_engine import KeywordEngine
from core.custom_keyword_loader import validate_code, write_keyword_file, reload_custom_keywords

router = APIRouter(prefix="/api", tags=["keywords"])


@router.get("/keywords", response_model=List[KeywordResponse])
def list_keywords(platform: str | None = None, category: str | None = None, db: Session = Depends(get_db)):
    return KeywordEngine.get_keywords(db, platform=platform, category=category)


@router.get("/keywords/categories", response_model=List[KeywordCategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    return KeywordEngine.get_categories(db)


@router.post("/projects/{project_id}/custom-keywords", response_model=KeywordResponse)
def create_custom_keyword(project_id: str, keyword: KeywordCreate, db: Session = Depends(get_db)):
    if keyword.code:
        valid, error = validate_code(keyword.code)
        if not valid:
            raise HTTPException(status_code=400, detail=f"Python syntax error: {error}")
        write_keyword_file(keyword.name, keyword.code)
        reload_custom_keywords()

    db_kw = Keyword(
        name=keyword.name,
        category="custom",
        platform=keyword.platform,
        params=keyword.params,
        description=keyword.description,
        code=keyword.code,
    )
    db.add(db_kw)
    db.commit()
    db.refresh(db_kw)
    return db_kw


@router.put("/keywords/{keyword_id}", response_model=KeywordResponse)
def update_custom_keyword(keyword_id: str, keyword: KeywordCreate, db: Session = Depends(get_db)):
    db_kw = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not db_kw:
        raise HTTPException(status_code=404, detail="Keyword not found")
    if db_kw.category != "custom":
        raise HTTPException(status_code=403, detail="Only custom keywords can be edited")

    if keyword.code:
        valid, error = validate_code(keyword.code)
        if not valid:
            raise HTTPException(status_code=400, detail=f"Python syntax error: {error}")
        write_keyword_file(keyword.name, keyword.code)
        reload_custom_keywords()

    db_kw.name = keyword.name
    db_kw.platform = keyword.platform
    db_kw.params = keyword.params
    db_kw.description = keyword.description
    db_kw.code = keyword.code
    db.commit()
    db.refresh(db_kw)
    return db_kw


@router.delete("/keywords/{keyword_id}")
def delete_custom_keyword(keyword_id: str, db: Session = Depends(get_db)):
    db_kw = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not db_kw:
        raise HTTPException(status_code=404, detail="Keyword not found")
    if db_kw.category != "custom":
        raise HTTPException(status_code=403, detail="Only custom keywords can be deleted")
    db.delete(db_kw)
    db.commit()
    return {"message": "Keyword deleted"}


@router.get("/projects/{project_id}/custom-keywords", response_model=List[KeywordResponse])
def list_custom_keywords(project_id: str, db: Session = Depends(get_db)):
    return db.query(Keyword).filter(Keyword.category == "custom").all()
```

- [ ] **Step 4: AndroidExecutor 支持自定义关键字**

在 `backend/executors/android_executor.py` 的 `_execute_keyword` 方法末尾（在最后的 `else` 分支之前）添加：

```python
            else:
                # Try custom keyword
                from core.custom_keyword_loader import load_custom_keyword_function
                custom_func = load_custom_keyword_function(keyword_name)
                if custom_func:
                    try:
                        element = None
                        if locator:
                            element = self._find_element(d, locator)
                        custom_func(d, element, params)
                        return True
                    except Exception as e:
                        self._log(f"Custom keyword {keyword_name} failed: {e}", "ERROR")
                        return False
                self._log(f"Unknown keyword: {keyword_name}", "ERROR")
                return False
```

- [ ] **Step 5: 编写并运行测试**

创建 `backend/tests/test_custom_keywords.py`：

```python
import pytest
from fastapi.testclient import TestClient
from main import app
from core.custom_keyword_loader import validate_code

client = TestClient(app)

def test_validate_valid_code():
    valid, error = validate_code("def test(): pass")
    assert valid is True
    assert error == ""

def test_validate_invalid_code():
    valid, error = validate_code("def test(: pass")
    assert valid is False
    assert "Syntax error" in error

def test_create_custom_keyword():
    response = client.post("/api/projects/default/custom-keywords", json={
        "name": "custom_click_test",
        "description": "Test custom keyword",
        "platform": "android",
        "code": "def custom_click_test(d, locator, params):\n    d.click(0.5, 0.5)\n",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "custom_click_test"
    assert data["category"] == "custom"

def test_create_custom_keyword_with_syntax_error():
    response = client.post("/api/projects/default/custom-keywords", json={
        "name": "bad_keyword",
        "description": "Bad keyword",
        "code": "def bad_keyword(:\n    pass\n",
    })
    assert response.status_code == 400
    assert "syntax error" in response.json()["detail"].lower()

def test_delete_custom_keyword():
    create_res = client.post("/api/projects/default/custom-keywords", json={
        "name": "delete_me",
        "description": "To delete",
        "code": "def delete_me(d, locator, params): pass",
    })
    kw_id = create_res.json()["id"]

    response = client.delete(f"/api/keywords/{kw_id}")
    assert response.status_code == 200

def test_cannot_delete_builtin_keyword():
    from db.database import SessionLocal
    from models.keyword import Keyword
    db = SessionLocal()
    kw = db.query(Keyword).filter(Keyword.name == "click").first()
    db.close()
    if kw:
        response = client.delete(f"/api/keywords/{kw.id}")
        assert response.status_code == 403
```

运行测试：

```bash
cd backend && pytest tests/test_custom_keywords.py -v
```

Expected: `PASS`

- [ ] **Step 6: Commit**

```bash
git add backend/models/keyword.py backend/schemas/keyword.py backend/api/keywords.py backend/core/custom_keyword_loader.py backend/db/init_db.py backend/executors/android_executor.py backend/tests/test_custom_keywords.py
git commit -m "feat: add custom keyword management with syntax validation and dynamic loading"
```

---

## 验证与收尾

### 最终验证清单

启动前后端后，按以下顺序验证：

- [ ] 侧边栏所有菜单显示中文
- [ ] Dashboard 四个统计数字正确（项目数、用例数、设备数、任务数）
- [ ] 项目管理页面：删除有数据的项目时弹窗提示禁止删除；删除无数据的项目时弹确认窗
- [ ] 项目详情页：添加页面/用例 Modal 正常工作，上传脚本有成功/失败提示
- [ ] PO 管理：创建 Page Object 弹窗顶部显示所属项目名
- [ ] APK 管理：列表加载正常，有错误提示而非一直 loading
- [ ] 用例管理：关键字分类正确加载，类型只有"关键字驱动"
- [ ] 脚本管理：上传有 loading 和消息提示
- [ ] 设备管理：USB 设备显示"连接"按钮，TCP/IP 设备显示"断开"按钮，无 TCP/IP 弹窗
- [ ] 任务管理：创建任务时"测试内容"下拉框分组显示用例和脚本，表格显示类型标签
- [ ] 关键字管理：可创建/编辑/删除自定义关键字，语法错误时拒绝保存
- [ ] 调试页面：全部中文，iframe 错误时有提示

### 数据库迁移说明

SQLite 不支持完整的 `ALTER TABLE`。修改 `test_tasks` 表结构（增加 `script_id`，`case_id` 改为 nullable）后，建议：

```bash
# 备份旧数据库
cp data/autotest.db data/autotest.db.bak
# 删除旧数据库，让 SQLAlchemy 重新创建（会丢失数据，仅开发环境适用）
rm data/autotest.db
# 重新启动后端，自动初始化
```

生产环境应使用 Alembic 等迁移工具。

---

*Plan generated on 2026-05-19*
