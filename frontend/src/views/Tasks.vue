<template>
  <div class="tasks">
    <a-page-header
      title="Tasks"
      sub-title="Manage test tasks"
    >
      <template #extra>
        <a-button type="primary" @click="showModal = true">Create Task</a-button>
      </template>
    </a-page-header>

    <a-table
      :columns="columns"
      :data-source="tasks"
      :loading="loading"
      row-key="id"
      style="margin-top: 24px"
    >
      <template #status="{ record }">
        <a-tag :color="getStatusColor(record.status)">
          {{ record.status }}
        </a-tag>
      </template>
      <template #action="{ record }">
        <a-button type="link" @click="executeTask(record.id)">Execute</a-button>
      </template>
    </a-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getTasks, executeTask as executeTaskApi } from '../api'

const tasks = ref([])
const loading = ref(false)
const showModal = ref(false)

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id' },
  { title: 'Case ID', dataIndex: 'case_id', key: 'case_id' },
  { title: 'Status', dataIndex: 'status', key: 'status', slots: { customRender: 'status' } },
  { title: 'Created', dataIndex: 'created_at', key: 'created_at' },
  { title: 'Action', key: 'action', slots: { customRender: 'action' } },
]

const getStatusColor = (status) => {
  const colors = {
    pending: 'default',
    running: 'blue',
    completed: 'green',
    failed: 'red',
  }
  return colors[status] || 'default'
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

const executeTask = async (id) => {
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
.tasks {
  padding: 24px;
}
</style>
