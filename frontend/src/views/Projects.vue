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
      <template #status="{ record }">
        <a-tag :color="record.status === 'enabled' ? 'success' : 'warning'">
          {{ record.status === 'enabled' ? '启用' : '禁用' }}
        </a-tag>
      </template>
      <template #action="{ record }">
        <a-button type="link" @click="viewProject(record.id)">查看</a-button>
        <a-button type="link" @click="toggleStatus(record)">{{ record.status === 'enabled' ? '禁用' : '启用' }}</a-button>
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
          <a-input v-model:value="form.name" placeholder="请输入项目名称" />
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-model:value="form.description" placeholder="请输入项目描述" :rows="3" />
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
import { message } from 'ant-design-vue'
import { getProjects, createProject, deleteProject as deleteProjectApi, getProjectStats, updateProject } from '../api'

const router = useRouter()
const projects = ref([])
const loading = ref(false)
const showModal = ref(false)
const form = ref({ name: '', description: '', platform: 'android' })

const columns = [
  { title: '项目名称', dataIndex: 'name', key: 'name' },
  { title: '平台', dataIndex: 'platform', key: 'platform' },
  { title: '状态', key: 'status', slots: { customRender: 'status' } },
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
    form.value = { name: '', description: '', platform: 'android' }
    fetchProjects()
    message.success('项目创建成功')
  } catch (error) {
    message.error('创建失败: ' + (error.response?.data?.detail || error.message))
  }
}

const viewProject = (id) => {
  router.push(`/projects/${id}`)
}

const toggleStatus = async (record) => {
  const newStatus = record.status === 'enabled' ? 'disabled' : 'enabled'
  try {
    await updateProject(record.id, { status: newStatus })
    record.status = newStatus
    message.success(`项目已${newStatus === 'enabled' ? '启用' : '禁用'}`)
  } catch (error) {
    message.error('操作失败: ' + (error.response?.data?.detail || error.message))
  }
}

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

const handleDeleteConfirm = async () => {
  if (pendingDeleteHasData.value) {
    showDeleteModal.value = false
    return
  }
  try {
    await deleteProjectApi(pendingDeleteId.value)
    showDeleteModal.value = false
    fetchProjects()
    message.success('删除成功')
  } catch (error) {
    message.error('删除失败: ' + (error.response?.data?.detail || error.message))
  }
}

fetchProjects()
</script>

<style scoped>
.projects {
  padding: 24px;
}
</style>