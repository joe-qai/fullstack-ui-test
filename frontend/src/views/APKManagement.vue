<template>
  <div class="apk-management">
    <a-page-header title="APK管理" sub-title="APK包版本管理" />

    <a-table :columns="columns" :data-source="apks" :loading="loading" row-key="id" style="margin-top: 16px">
      <template #fileSize="{ record }">{{ formatSize(record.file_size) }}</template>
      <template #action="{ record }">
        <a-popconfirm title="确定删除此APK版本?" @confirm="handleDelete(record.id)">
          <a-button type="link" danger>删除</a-button>
        </a-popconfirm>
      </template>
    </a-table>
    <a-empty v-if="!loading && apks.length === 0" description="暂无APK文件" style="margin-top: 48px" />

    <a-button type="primary" @click="showUploadModal = true" style="margin-top: 16px">上传新APK</a-button>

    <a-modal v-model:open="showUploadModal" title="上传APK" @ok="handleUpload" :confirmLoading="uploading">
      <a-form :model="uploadForm" layout="vertical">
        <a-form-item label="APK文件" required>
          <a-upload :before-upload="beforeUpload" accept=".apk" :maxCount="1" :fileList="fileList" @remove="handleRemove">
            <a-button>选择APK文件</a-button>
          </a-upload>
        </a-form-item>
        <a-form-item label="版本号">
          <a-input v-model:value="uploadForm.version" placeholder="请输入版本号" />
        </a-form-item>
        <a-form-item label="备注">
          <a-input v-model:value="uploadForm.description" placeholder="可选" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { getApks, uploadApk, deleteApk } from '../api'

const apks = ref([])
const loading = ref(false)
const uploading = ref(false)
const showUploadModal = ref(false)
const fileList = ref([])
const apkFile = ref(null)
const uploadForm = ref({ version: '', description: '' })

const columns = [
  { title: '文件名', dataIndex: 'file_name', key: 'file_name' },
  { title: '包名', dataIndex: 'package_name', key: 'package_name' },
  { title: '版本', dataIndex: 'version', key: 'version' },
  { title: '大小', key: 'file_size', slots: { customRender: 'fileSize' } },
  { title: '备注', dataIndex: 'description', key: 'description' },
  { title: '上传时间', dataIndex: 'uploaded_at', key: 'uploaded_at' },
  { title: '操作', key: 'action', slots: { customRender: 'action' } },
]

const formatSize = (bytes) => {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getApks()
    apks.value = res.data
  } catch (error) {
    message.error('获取APK列表失败: ' + (error.response?.data?.detail || error.message))
    apks.value = []
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
    await uploadApk(apkFile.value, uploadForm.value.version, uploadForm.value.description)
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

const handleDelete = async (apkId) => {
  try {
    await deleteApk(apkId)
    fetchData()
  } catch (error) {
    console.error('Failed to delete APK:', error)
  }
}

onMounted(fetchData)
</script>

<style scoped>
.apk-management { padding: 24px; }
</style>