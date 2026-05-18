<template>
  <div class="apk-management">
    <a-page-header title="APK管理" sub-title="项目内APK版本管理">
      <template #extra>
        <a-select v-model:value="selectedProject" style="width: 200px" placeholder="选择项目" @change="fetchData">
          <a-select-option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</a-select-option>
        </a-select>
      </template>
    </a-page-header>

    <a-table v-if="selectedProject" :columns="columns" :data-source="apks" :loading="loading" row-key="id" style="margin-top: 16px">
      <template #fileSize="{ record }">{{ formatSize(record.file_size) }}</template>
      <template #action="{ record }">
        <a-popconfirm title="确定删除此APK版本?" @confirm="handleDelete(record.id)">
          <a-button type="link" danger>删除</a-button>
        </a-popconfirm>
      </template>
    </a-table>
    <a-empty v-else description="请先选择项目" style="margin-top: 48px" />

    <a-button v-if="selectedProject" type="primary" @click="showUploadModal = true" style="margin-top: 16px">上传新APK</a-button>

    <a-modal v-model:open="showUploadModal" title="上传APK" @ok="handleUpload" :confirmLoading="uploading">
      <a-form :model="uploadForm" layout="vertical">
        <a-form-item label="APK文件" required>
          <a-upload :before-upload="beforeUpload" accept=".apk" :maxCount="1" :fileList="fileList" @remove="handleRemove">
            <a-button>选择APK文件</a-button>
          </a-upload>
        </a-form-item>
        <a-form-item label="版本号">
          <a-input v-model:value="uploadForm.version" placeholder="自动从APK解析，也可手动填写" />
        </a-form-item>
        <a-form-item label="版本备注">
          <a-input v-model:value="uploadForm.description" placeholder="可选" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getProjects, getApks, uploadApk, deleteApk } from '../api'

const projects = ref([])
const selectedProject = ref(null)
const apks = ref([])
const loading = ref(false)
const uploading = ref(false)
const showUploadModal = ref(false)
const fileList = ref([])
const apkFile = ref(null)
const uploadForm = ref({ version: '', description: '' })

const columns = [
  { title: '版本', dataIndex: 'version', key: 'version' },
  { title: '包名', dataIndex: 'package_name', key: 'package_name' },
  { title: '大小', key: 'file_size', slots: { customRender: 'fileSize' } },
  { title: '上传时间', dataIndex: 'uploaded_at', key: 'uploaded_at' },
  { title: '备注', dataIndex: 'description', key: 'description' },
  { title: '操作', key: 'action', slots: { customRender: 'action' } },
]

const formatSize = (bytes) => {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const fetchData = async () => {
  if (!selectedProject.value) return
  loading.value = true
  try {
    const res = await getApks(selectedProject.value)
    apks.value = res.data
  } catch (error) {
    console.error('Failed to fetch APKs:', error)
  } finally {
    loading.value = false
  }
}

const beforeUpload = (file) => {
  apkFile.value = file
  fileList.value = [file]
  return false
}

const handleRemove = () => {
  apkFile.value = null
  fileList.value = []
}

const handleUpload = async () => {
  if (!apkFile.value) return
  uploading.value = true
  try {
    await uploadApk(selectedProject.value, apkFile.value, uploadForm.value.version, uploadForm.value.description)
    showUploadModal.value = false
    apkFile.value = null
    fileList.value = []
    uploadForm.value = { version: '', description: '' }
    fetchData()
  } catch (error) {
    console.error('Failed to upload APK:', error)
  } finally {
    uploading.value = false
  }
}

const handleDelete = async (apkId) => {
  try {
    await deleteApk(selectedProject.value, apkId)
    fetchData()
  } catch (error) {
    console.error('Failed to delete APK:', error)
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
.apk-management { padding: 24px; }
</style>