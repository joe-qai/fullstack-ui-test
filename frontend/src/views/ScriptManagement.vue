<template>
  <div class="script-management">
    <a-page-header title="脚本管理" sub-title="Python脚本上传与管理">
      <template #extra>
        <a-button v-if="selectedRowKeys.length > 0" danger @click="handleBatchDelete" style="margin-right: 8px">
          批量删除 ({{ selectedRowKeys.length }})
        </a-button>
        <a-button type="primary" @click="showUploadModal = true" :loading="uploading">
          <template #icon><PlusOutlined /></template>
          上传脚本
        </a-button>
      </template>
    </a-page-header>

    <a-table :columns="columns" :data-source="scripts" :loading="loading" row-key="id" style="margin-top: 16px"
      :expandable="{ expandedRowRender: expandScript }"
      :row-selection="{ selectedRowKeys: selectedRowKeys, onChange: onSelectChange }">
      <template #project="{ record }">{{ getProjectName(record.project_id) }}</template>
      <template #uploadedAt="{ record }">{{ formatDate(record.uploaded_at) }}</template>
      <template #action="{ record }">
        <a-tooltip title="编辑">
          <a-button type="link" @click="handleEdit(record)">
            <template #icon><EditOutlined /></template>
          </a-button>
        </a-tooltip>
        <a-tooltip title="下载">
          <a-button type="link" @click="handleDownload(record)">
            <template #icon><DownloadOutlined /></template>
          </a-button>
        </a-tooltip>
        <a-popconfirm title="确定删除?" @confirm="handleDelete(record.id, record.project_id)">
          <a-tooltip title="删除">
            <a-button type="link" danger>
              <template #icon><DeleteOutlined /></template>
            </a-button>
          </a-tooltip>
        </a-popconfirm>
      </template>
    </a-table>

    <a-empty v-if="!loading && scripts.length === 0" description="暂无脚本" style="margin-top: 48px" />

    <!-- 上传弹窗 -->
    <a-modal v-model:open="showUploadModal" title="上传脚本" @ok="handleUpload" @cancel="resetForm" :confirm-loading="uploading">
      <a-form :model="uploadForm" layout="vertical">
        <a-form-item label="选择项目" :required="true">
          <a-select v-model:value="uploadForm.project_id" placeholder="请选择项目">
            <a-select-option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="脚本文件" :required="true">
          <a-upload :custom-request="handleFileSelect" accept=".py" :show-upload-list="false">
            <a-button>
              <template #icon><UploadOutlined /></template>
              {{ uploadForm.file ? uploadForm.file.name : '选择文件' }}
            </a-button>
          </a-upload>
        </a-form-item>
        <a-form-item label="版本号">
          <a-input v-model:value="uploadForm.version" placeholder="如：1.0.0" />
        </a-form-item>
        <a-form-item label="备注">
          <a-textarea v-model:value="uploadForm.description" placeholder="请输入备注信息" :rows="3" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 编辑脚本内容弹窗 -->
    <a-modal v-model:open="showEditModal" title="编辑脚本内容" width="800px" @ok="handleEditConfirm" :confirm-loading="editLoading">
      <a-form :model="editForm" layout="vertical">
        <a-form-item label="脚本名称">
          <a-input v-model:value="editForm.name" disabled />
        </a-form-item>
        <a-form-item label="脚本内容">
          <div class="code-editor-wrapper">
            <textarea v-model="editForm.content" class="code-editor" spellcheck="false" @keydown="handleEditorKeydown"></textarea>
          </div>
        </a-form-item>
        <a-form-item v-if="syntaxError" style="color: red; margin-bottom: 0">
          <span>{{ syntaxError }}</span>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted, h, reactive, nextTick } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined, UploadOutlined, EditOutlined, DownloadOutlined, DeleteOutlined } from '@ant-design/icons-vue'
import { getProjects, getAllScripts, uploadScript, updateScript, deleteScript as deleteScriptApi, batchDeleteScripts, getScriptDownloadUrl, getScriptContent, updateScriptContent } from '../api'
import { formatDate } from '../utils/format'

const projects = ref([])
const scripts = ref([])
const loading = ref(false)
const uploading = ref(false)
const showUploadModal = ref(false)
const selectedRowKeys = ref([])
const showEditModal = ref(false)
const editLoading = ref(false)
const editingScript = ref(null)
const editForm = reactive({ name: '', description: '', content: '' })
const syntaxError = ref('')

const uploadForm = reactive({
  project_id: null,
  file: null,
  version: '',
  description: ''
})

const columns = [
  { title: '名称', dataIndex: 'name', key: 'name' },
  { title: '所属项目', key: 'project', slots: { customRender: 'project' } },
  { title: '版本', dataIndex: 'version', key: 'version' },
  { title: '类型', dataIndex: 'type', key: 'type' },
  { title: '上传时间', key: 'uploadedAt', slots: { customRender: 'uploadedAt' }, width: 160 },
  { title: '操作', key: 'action', slots: { customRender: 'action' } },
]

const onSelectChange = (keys) => { selectedRowKeys.value = keys }

const expandScript = ({ record }) => {
  let classes = []
  let methods = []
  try { classes = JSON.parse(record.classes || '[]') } catch {}
  try { methods = JSON.parse(record.methods || '[]') } catch {}
  return h('div', { style: { padding: '8px 16px' } }, [
    h('p', { style: { margin: '4px 0' } }, [`文件路径: ${record.file_path}`]),
    record.description ? h('p', { style: { margin: '4px 0' } }, [`备注: ${record.description}`]) : null,
    classes.length > 0 ? h('p', { style: { margin: '4px 0' } }, [`类: ${classes.join(', ')}`]) : null,
    methods.length > 0 ? h('p', { style: { margin: '4px 0' } }, [`方法: ${methods.join(', ')}`]) : null,
  ])
}

const getProjectName = (projectId) => {
  const p = projects.value.find(p => p.id === projectId)
  return p ? p.name : projectId
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getAllScripts()
    scripts.value = res.data
    selectedRowKeys.value = []
  } catch (error) {
    console.error('Failed to fetch scripts:', error)
  } finally {
    loading.value = false
  }
}

const handleFileSelect = ({ file }) => {
  uploadForm.file = file
}

const resetForm = () => {
  uploadForm.project_id = null
  uploadForm.file = null
  uploadForm.version = ''
  uploadForm.description = ''
}

const handleUpload = async () => {
  if (!uploadForm.project_id) {
    message.error('请选择项目')
    return
  }
  if (!uploadForm.file) {
    message.error('请选择脚本文件')
    return
  }
  
  uploading.value = true
  try {
    await uploadScript(uploadForm.project_id, uploadForm.file)
    message.success('脚本上传成功')
    showUploadModal.value = false
    resetForm()
    fetchData()
  } catch (error) {
    message.error('脚本上传失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    uploading.value = false
  }
}

const handleEdit = async (record) => {
  editingScript.value = record
  editForm.name = record.name
  editForm.description = record.description || ''
  editForm.content = ''
  syntaxError.value = ''
  showEditModal.value = true
  try {
    const res = await getScriptContent(record.project_id, record.id)
    editForm.content = res.data.content
  } catch (error) {
    message.error('加载脚本内容失败: ' + (error.response?.data?.detail || error.message))
  }
}

const handleEditorKeydown = (e) => {
  if (e.key === 'Tab') {
    e.preventDefault()
    const start = e.target.selectionStart
    const end = e.target.selectionEnd
    editForm.content = editForm.content.substring(0, start) + '    ' + editForm.content.substring(end)
    nextTick(() => {
      e.target.selectionStart = e.target.selectionEnd = start + 4
    })
  }
}

const handleEditConfirm = async () => {
  if (!editingScript.value) return
  editLoading.value = true
  syntaxError.value = ''
  try {
    await updateScriptContent(editingScript.value.project_id, editingScript.value.id, editForm.content)
    message.success('保存成功')
    showEditModal.value = false
    fetchData()
  } catch (error) {
    syntaxError.value = error.response?.data?.detail || error.message
  } finally {
    editLoading.value = false
  }
}

const handleDownload = (record) => {
  const url = getScriptDownloadUrl(record.project_id, record.id)
  window.open(url, '_blank')
}

const handleDelete = async (scriptId, projectId) => {
  try {
    await deleteScriptApi(projectId, scriptId)
    fetchData()
  } catch (error) {
    console.error('Failed to delete script:', error)
  }
}

const handleBatchDelete = async () => {
  const ids = selectedRowKeys.value
  if (ids.length === 0) return
  try {
    const res = await batchDeleteScripts(ids)
    message.success(`成功删除 ${res.data.count} 个脚本`)
    fetchData()
  } catch (error) {
    message.error('批量删除失败: ' + (error.response?.data?.detail || error.message))
  }
}

onMounted(async () => {
  try {
    const res = await getProjects()
    projects.value = res.data
  } catch (error) {
    console.error('Failed to fetch projects:', error)
  }
  fetchData()
})
</script>

<style scoped>
.script-management { padding: 24px; }
.code-editor-wrapper { border: 1px solid #d9d9d9; border-radius: 6px; overflow: hidden; }
.code-editor { width: 100%; min-height: 400px; font-family: 'Consolas', 'Courier New', monospace; font-size: 13px; line-height: 1.6; padding: 12px; border: none; outline: none; resize: vertical; tab-size: 4; background: #1e1e1e; color: #d4d4d4; }
.code-editor:focus { border-color: #4096ff; }
</style>
