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