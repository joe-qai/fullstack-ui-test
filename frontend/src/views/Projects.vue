<template>
  <div class="projects">
    <a-page-header
      title="Projects"
      sub-title="Manage your test projects"
    >
      <template #extra>
        <a-button type="primary" @click="showModal = true">Create Project</a-button>
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
        <a-button type="link" @click="viewProject(record.id)">View</a-button>
        <a-button type="link" danger @click="deleteProject(record.id)">Delete</a-button>
      </template>
    </a-table>

    <a-modal
      v-model:open="showModal"
      title="Create Project"
      @ok="handleCreate"
    >
      <a-form :model="form" layout="vertical">
        <a-form-item label="Name" required>
          <a-input v-model:value="form.name" />
        </a-form-item>
        <a-form-item label="App ID">
          <a-input v-model:value="form.app_id" />
        </a-form-item>
        <a-form-item label="Platform">
          <a-select v-model:value="form.platform">
            <a-select-option value="android">Android</a-select-option>
            <a-select-option value="ios">iOS</a-select-option>
            <a-select-option value="web">Web</a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getProjects, createProject, deleteProject as deleteProjectApi } from '../api'

const router = useRouter()
const projects = ref([])
const loading = ref(false)
const showModal = ref(false)
const form = ref({ name: '', app_id: '', platform: 'android' })

const columns = [
  { title: 'Name', dataIndex: 'name', key: 'name' },
  { title: 'App ID', dataIndex: 'app_id', key: 'app_id' },
  { title: 'Platform', dataIndex: 'platform', key: 'platform' },
  { title: 'Created', dataIndex: 'created_at', key: 'created_at' },
  { title: 'Action', key: 'action', slots: { customRender: 'action' } },
]

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

const deleteProject = async (id) => {
  try {
    await deleteProjectApi(id)
    fetchProjects()
  } catch (error) {
    console.error('Failed to delete project:', error)
  }
}

onMounted(fetchProjects)
</script>

<style scoped>
.projects {
  padding: 24px;
}
</style>
