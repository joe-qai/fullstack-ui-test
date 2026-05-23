<template>
  <div class="reports-container">
    <a-page-header title="报告管理" sub-title="测试报告查看与下载">
      <template #extra>
        <a-input-search v-model:value="searchText" placeholder="搜索报告名称或任务ID" style="width: 280px; margin-right: 12px" @search="fetchReports" />
        <a-button v-if="selectedRowKeys.length > 0" danger @click="handleBatchDelete">
          批量删除 ({{ selectedRowKeys.length }})
        </a-button>
      </template>
    </a-page-header>

    <a-table :columns="columns" :data-source="filteredReports" :loading="loading" row-key="id" style="margin-top: 16px"
      :row-selection="{ selectedRowKeys: selectedRowKeys, onChange: onSelectChange }">
      <template #taskId="{ record }">
        <a-tooltip :title="record.task_id">
          <span class="task-id-text">{{ record.task_id?.length > 16 ? record.task_id.substring(0, 16) + '...' : record.task_id }}</span>
        </a-tooltip>
      </template>
      <template #taskStatus="{ record }">
        <a-tag :color="getStatusColor(record.task_status)">{{ getStatusText(record.task_status) }}</a-tag>
      </template>
      <template #executionTime="{ record }">{{ formatDate(record.execution_time) }}</template>
      <template #createdAt="{ record }">{{ formatDate(record.created_at) }}</template>
      <template #action="{ record }">
        <a-tooltip title="查看">
          <a-button type="link" @click="viewReport(record.id)">
            <template #icon><EyeOutlined /></template>
          </a-button>
        </a-tooltip>
        <a-tooltip title="下载">
          <a-button type="link" @click="downloadReport(record.id, 'html')">
            <template #icon><DownloadOutlined /></template>
          </a-button>
        </a-tooltip>
        <a-popconfirm title="确定删除?" @confirm="handleDelete(record.id)">
          <a-tooltip title="删除">
            <a-button type="link" danger>
              <template #icon><DeleteOutlined /></template>
            </a-button>
          </a-tooltip>
        </a-popconfirm>
      </template>
    </a-table>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { getReports, deleteReport, batchDeleteReports, getReportDownloadUrl, getReportViewUrl } from '../api'
import { formatDate } from '../utils/format'
import { EyeOutlined, DownloadOutlined, DeleteOutlined } from '@ant-design/icons-vue'

const reports = ref([])
const loading = ref(false)
const selectedRowKeys = ref([])
const searchText = ref('')

const columns = [
  { title: '报告名称', dataIndex: 'name', key: 'name' },
  { title: '任务ID', key: 'taskId', slots: { customRender: 'taskId' } },
  { title: '执行时间', key: 'executionTime', slots: { customRender: 'executionTime' }, width: 180 },
  { title: '任务状态', key: 'taskStatus', slots: { customRender: 'taskStatus' }, width: 100 },
  { title: '创建时间', key: 'createdAt', slots: { customRender: 'createdAt' }, width: 160 },
  { title: '操作', key: 'action', slots: { customRender: 'action' }, width: 200 },
]

const getStatusColor = (status) => {
  const colors = { pending: 'default', running: 'blue', completed: 'green', failed: 'red', cancelled: 'orange' }
  return colors[status] || 'default'
}

const getStatusText = (status) => {
  const texts = { pending: '待执行', running: '执行中', completed: '已完成', failed: '失败', cancelled: '已取消' }
  return texts[status] || status || '-'
}

const filteredReports = computed(() => {
  if (!searchText.value) return reports.value
  const q = searchText.value.toLowerCase()
  return reports.value.filter(r =>
    (r.name && r.name.toLowerCase().includes(q)) ||
    (r.task_id && r.task_id.toLowerCase().includes(q))
  )
})

const onSelectChange = (keys) => { selectedRowKeys.value = keys }

const fetchReports = async () => {
  loading.value = true
  try {
    const res = await getReports()
    reports.value = res.data
    selectedRowKeys.value = []
  } catch (error) {
    message.error('获取报告列表失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

const viewReport = (reportId) => {
  window.open(getReportViewUrl(reportId), '_blank')
}

const downloadReport = (reportId, format) => {
  window.open(getReportDownloadUrl(reportId, format), '_blank')
}

const handleDelete = async (reportId) => {
  try {
    await deleteReport(reportId)
    fetchReports()
  } catch (error) {
    message.error('删除失败: ' + (error.response?.data?.detail || error.message))
  }
}

const handleBatchDelete = async () => {
  const ids = selectedRowKeys.value
  if (ids.length === 0) return
  try {
    const res = await batchDeleteReports(ids)
    message.success(`成功删除 ${res.data.count} 个报告`)
    fetchReports()
  } catch (error) {
    message.error('批量删除失败: ' + (error.response?.data?.detail || error.message))
  }
}

onMounted(fetchReports)
</script>

<style scoped>
.reports-container { padding: 24px; }
.task-id-text { font-family: monospace; font-size: 12px; color: #888; cursor: default; }
</style>
