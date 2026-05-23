<template>
  <div class="tasks">
    <a-page-header title="任务管理" sub-title="执行测试任务">
      <template #extra>
        <a-button v-if="selectedRowKeys.length > 0" danger @click="handleBatchDelete" style="margin-right: 8px">
          批量删除 ({{ selectedRowKeys.length }})
        </a-button>
        <a-button type="primary" @click="openCreateModal">创建任务</a-button>
      </template>
    </a-page-header>

    <a-table :columns="columns" :data-source="tasks" :loading="loading" row-key="id" style="margin-top: 16px"
      :row-selection="{ selectedRowKeys: selectedRowKeys, onChange: onSelectChange }"
      :row-class-name="getRowClass">
      <template #contentName="{ record }">{{ getContentName(record) }}</template>
      <template #contentType="{ record }">
        <a-tag :color="record.case_id ? 'blue' : 'orange'">{{ record.case_id ? '用例' : '脚本' }}</a-tag>
      </template>
      <template #apkVersion="{ record }">{{ getApkLabel(record.apk_id) }}</template>
      <template #status="{ record }">
        <a-tag :color="getStatusColor(record.status)">{{ getStatusText(record.status) }}</a-tag>
      </template>
      <template #failureReason="{ record }">
        <span :style="{ color: record.status === 'completed' ? '#52c41a' : '#ff4d4f' }">
          {{ getFailureReason(record) }}
        </span>
      </template>
      <template #action="{ record }">
        <a-popconfirm v-if="record.status === 'running'" title="确定中止?" @confirm="handleAbort(record.id)">
          <a-button type="link" danger>中止</a-button>
        </a-popconfirm>
        <a-popconfirm v-if="canDelete(record)" title="确定删除?" @confirm="handleDelete(record.id)">
          <a-button type="link" danger>删除</a-button>
        </a-popconfirm>
      </template>
    </a-table>

    <a-modal v-model:open="showCreateModal" title="创建任务" @ok="handleCreateTask" :confirm-loading="creating">
      <a-form :model="taskForm" layout="vertical">
        <a-form-item label="项目" required>
          <a-select v-model:value="taskForm.projectId" placeholder="选择项目" @change="onProjectChange">
            <a-select-option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="测试用例" required>
          <a-select v-model:value="taskForm.content_id" placeholder="选择用例或脚本">
            <a-select-opt-group label="用例">
              <a-select-option v-for="c in projectCases" :key="`case-${c.id}`" :value="`case-${c.id}`">{{ c.name }}</a-select-option>
            </a-select-opt-group>
            <a-select-opt-group label="脚本">
              <a-select-option v-for="s in projectScripts" :key="`script-${s.id}`" :value="`script-${s.id}`">{{ s.name }}</a-select-option>
            </a-select-opt-group>
          </a-select>
        </a-form-item>
        <a-form-item label="APK包">
          <a-select v-model:value="taskForm.apk_id" placeholder="选择APK包" allowClear>
            <a-select-option :value="null">不安装APK</a-select-option>
            <a-select-option v-for="apk in projectApks" :key="apk.id" :value="apk.id">
              {{ apk.file_name || apk.name }} {{ apk.version }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="目标设备" required>
          <template v-if="devicesLoading">
            <a-spin size="small" /> 加载设备中...
          </template>
          <template v-else-if="onlineDevices.length === 0">
            <a-empty description="暂无在线设备，请先连接设备" />
          </template>
          <a-checkbox-group v-else v-model:value="taskForm.device_ids">
            <a-checkbox v-for="d in onlineDevices" :key="d.id" :value="d.id">
              {{ d.name || d.serial }} 
              <a-tag :color="d.status === 'online' ? 'green' : 'red'" size="small">
                {{ d.status === 'online' ? '在线' : '离线' }}
              </a-tag>
              <span v-if="d.serial?.includes(':')" class="ml-1">
                <a-tag color="blue" size="small">TCP/IP</a-tag>
              </span>
            </a-checkbox>
          </a-checkbox-group>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import {
  getProjects, getAllCases, getAllScripts, getApks, getDevices, getTasks,
  createTask, executeTask as executeTaskApi,
  deleteTask as deleteTaskApi, batchDeleteTasks as batchDeleteTasksApi,
} from '../api'
import axios from 'axios'

const tasks = ref([])
const projects = ref([])
const projectCases = ref([])
const projectScripts = ref([])
const projectApks = ref([])
const devices = ref([])
const loading = ref(false)
const creating = ref(false)
const devicesLoading = ref(false)
const showCreateModal = ref(false)
const selectedRowKeys = ref([])

const taskForm = ref({
  projectId: null,
  content_id: null,
  apk_id: null,
  device_ids: [],
})

const onlineDevices = computed(() => devices.value.filter(d => d.status === 'online'))

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 120 },
  { title: '测试标题', key: 'contentName', slots: { customRender: 'contentName' } },
  { title: '类型', key: 'contentType', slots: { customRender: 'contentType' } },
  { title: 'APK包', key: 'apkVersion', slots: { customRender: 'apkVersion' } },
  { title: '状态', dataIndex: 'status', key: 'status', slots: { customRender: 'status' } },
  { title: '备注', key: 'failureReason', slots: { customRender: 'failureReason' }, ellipsis: true, width: 300 },
  { title: '创建时间', dataIndex: 'created_at', key: 'created_at' },
  { title: '操作', key: 'action', slots: { customRender: 'action' } },
]

const getStatusColor = (status) => {
  const colors = { pending: 'default', running: 'blue', completed: 'green', failed: 'red', cancelled: 'orange' }
  return colors[status] || 'default'
}

const getStatusText = (status) => {
  const texts = { pending: '待执行', running: '执行中', completed: '已完成', failed: '失败', cancelled: '已取消' }
  return texts[status] || status
}

const canDelete = (record) => ['completed', 'cancelled', 'failed'].includes(record.status)

const getRowClass = (record) => {
  if (record.status === 'running') return 'row-running'
  return ''
}

const onSelectChange = (keys) => { selectedRowKeys.value = keys }

const getContentName = (record) => {
  // 优先使用后端返回的名称
  if (record.content_name) {
    return record.content_name
  }
  // 降级到本地查找
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
  return apk ? `${apk.file_name || apk.name} ${apk.version}` : apkId
}

const getFailureReason = (record) => {
  // 成功时显示空
  if (record.status === 'completed') {
    return ''
  }
  // 优先使用后端返回的error_message
  if (record.error_message) {
    return record.error_message
  }
  // 查找第一个失败的结果的错误信息
  if (record.results && record.results.length > 0) {
    const failedResult = record.results.find(r => r.status === 'failed' && r.error_message)
    if (failedResult) {
      return failedResult.error_message
    }
    // 如果有失败的步骤，显示步骤信息
    const failedStep = record.results.find(r => r.steps && r.steps.some(s => s.status === 'failed'))
    if (failedStep && failedStep.steps) {
      const step = failedStep.steps.find(s => s.status === 'failed')
      if (step && step.error) {
        return step.error
      }
    }
  }
  return '执行失败'
}

const fetchTasks = async () => {
  loading.value = true
  try {
    const res = await getTasks()
    // 对于每个任务，获取详细的结果，包含错误信息
    const tasksWithDetails = await Promise.all(
      res.data.map(async (task) => {
        try {
          const reportRes = await axios.get(`/api/tasks/${task.id}/reports`)
          return { ...task, results: reportRes.data.results || [] }
        } catch {
          return { ...task, results: [] }
        }
      })
    )
    tasks.value = tasksWithDetails
    selectedRowKeys.value = []
  } catch (error) {
    console.error('Failed to fetch tasks:', error)
  } finally {
    loading.value = false
  }
}

const openCreateModal = async () => {
  taskForm.value = { projectId: null, content_id: null, apk_id: null, device_ids: [] }
  showCreateModal.value = true
  devicesLoading.value = true
  projectScripts.value = []
  projectCases.value = []
  try {
    const [projRes, devRes, apkRes, scriptsRes, casesRes] = await Promise.all([
      getProjects(), getDevices(), getApks(), getAllScripts(), getAllCases(),
    ])
    projects.value = projRes.data
    devices.value = devRes.data
    projectApks.value = apkRes.data
    projectScripts.value = scriptsRes.data
    projectCases.value = casesRes.data
  } catch (error) {
    console.error('Failed to load modal data:', error)
    message.error('加载数据失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    devicesLoading.value = false
  }
}

const onProjectChange = async (projectId) => {
  taskForm.value.content_id = null
}

const handleCreateTask = async () => {
  if (!taskForm.value.content_id) {
    message.warning('请选择测试内容')
    return
  }
  if (taskForm.value.device_ids.length === 0) {
    message.warning('请选择至少一个目标设备')
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
    const res = await createTask(payload)
    showCreateModal.value = false
    message.success('任务创建成功，正在执行...')
    const execRes = await executeTaskApi(res.data.id)
    fetchTasks()
    
    // 检测是否有 ModuleNotFoundError 的友好提示
    if (execRes.data && execRes.data.results) {
      for (const deviceId in execRes.data.results) {
        const result = execRes.data.results[deviceId]
        if (result.error && result.error.endsWith('未安装！')) {
          message.error(result.error)
          break
        }
      }
    }
  } catch (error) {
    console.error('Failed to create task:', error)
    message.error('创建失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    creating.value = false
  }
}

const handleDelete = async (id) => {
  try {
    await deleteTaskApi(id)
    fetchTasks()
  } catch (error) {
    message.error('删除失败: ' + (error.response?.data?.detail || error.message))
  }
}

const handleBatchDelete = async () => {
  const ids = selectedRowKeys.value
  if (ids.length === 0) return
  try {
    const res = await batchDeleteTasksApi(ids)
    message.success(`成功删除 ${res.data.count} 个任务`)
    fetchTasks()
  } catch (error) {
    message.error('批量删除失败: ' + (error.response?.data?.detail || error.message))
  }
}

onMounted(fetchTasks)
</script>

<style scoped>
.tasks { padding: 24px; }
.ml-1 { margin-left: 4px; }
</style>