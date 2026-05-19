<template>
  <div class="script-management">
    <a-page-header title="脚本管理" sub-title="Python脚本上传与管理">
      <template #extra>
        <a-select v-model:value="selectedProject" style="width: 200px" placeholder="选择项目" @change="fetchData">
          <a-select-option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</a-select-option>
        </a-select>
      </template>
    </a-page-header>

    <a-table v-if="selectedProject" :columns="columns" :data-source="scripts" :loading="loading" row-key="id" style="margin-top: 16px"
      :expandable="{ expandedRowRender: expandScript }">
      <template #action="{ record }">
        <a-popconfirm title="确定删除?" @confirm="handleDelete(record.id)">
          <a-button type="link" danger>删除</a-button>
        </a-popconfirm>
      </template>
    </a-table>
    <a-empty v-else description="请先选择项目" style="margin-top: 48px" />

    <a-upload v-if="selectedProject" :custom-request="handleUpload" accept=".py" style="margin-top: 16px" :show-upload-list="false">
      <a-button type="primary" :loading="uploading">上传脚本</a-button>
    </a-upload>
  </div>
</template>

<script setup>
import { ref, onMounted, h } from 'vue'
import { message } from 'ant-design-vue'
import { getProjects, getScripts, uploadScript, deleteScript as deleteScriptApi } from '../api'

const projects = ref([])
const selectedProject = ref(null)
const scripts = ref([])
const loading = ref(false)
const uploading = ref(false)

const columns = [
  { title: '名称', dataIndex: 'name', key: 'name' },
  { title: '类型', dataIndex: 'type', key: 'type' },
  { title: '上传时间', dataIndex: 'uploaded_at', key: 'uploaded_at' },
  { title: '操作', key: 'action', slots: { customRender: 'action' } },
]

const expandScript = ({ record }) => {
  let classes = []
  let methods = []
  try { classes = JSON.parse(record.classes || '[]') } catch {}
  try { methods = JSON.parse(record.methods || '[]') } catch {}
  return h('div', { style: { padding: '8px 16px' } }, [
    h('p', { style: { margin: '4px 0' } }, [`文件路径: ${record.file_path}`]),
    classes.length > 0 ? h('p', { style: { margin: '4px 0' } }, [`类: ${classes.join(', ')}`]) : null,
    methods.length > 0 ? h('p', { style: { margin: '4px 0' } }, [`方法: ${methods.join(', ')}`]) : null,
  ])
}

const fetchData = async () => {
  if (!selectedProject.value) return
  loading.value = true
  try {
    const res = await getScripts(selectedProject.value)
    scripts.value = res.data
  } catch (error) {
    console.error('Failed to fetch scripts:', error)
  } finally {
    loading.value = false
  }
}

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

const handleDelete = async (scriptId) => {
  try {
    await deleteScriptApi(selectedProject.value, scriptId)
    fetchData()
  } catch (error) {
    console.error('Failed to delete script:', error)
  }
}

onMounted(async () => {
  try {
    const res = await getProjects()
    projects.value = res.data
    if (projects.value.length > 0) {
      selectedProject.value = projects.value[0].id
      fetchData()
    }
  } catch (error) {
    console.error('Failed to fetch projects:', error)
  }
})
</script>

<style scoped>
.script-management { padding: 24px; }
</style>