<template>
  <div class="project-detail">
    <a-page-header
      :title="project?.name || 'Project Detail'"
      sub-title="Manage project details"
      @back="goBack"
    />

    <a-tabs v-model:activeKey="activeKey" style="margin-top: 24px">
      <a-tab-pane key="pages" tab="Page Objects">
        <a-button type="primary" @click="showPageModal = true" style="margin-bottom: 16px">
          Add Page
        </a-button>
        <a-list :data-source="pages" row-key="id">
          <template #renderItem="{ item }">
            <a-list-item>
              <a-list-item-meta
                :title="item.name"
                :description="item.description"
              />
            </a-list-item>
          </template>
        </a-list>
      </a-tab-pane>

      <a-tab-pane key="cases" tab="Test Cases">
        <a-button type="primary" @click="showCaseModal = true" style="margin-bottom: 16px">
          Add Case
        </a-button>
        <a-list :data-source="cases" row-key="id">
          <template #renderItem="{ item }">
            <a-list-item>
              <a-list-item-meta
                :title="item.name"
                :description="item.type"
              />
            </a-list-item>
          </template>
        </a-list>
      </a-tab-pane>

      <a-tab-pane key="scripts" tab="Scripts">
        <a-upload
          :custom-request="handleUpload"
          accept=".py"
          style="margin-bottom: 16px"
        >
          <a-button>Upload Script</a-button>
        </a-upload>
        <a-list :data-source="scripts" row-key="id">
          <template #renderItem="{ item }">
            <a-list-item>
              <a-list-item-meta
                :title="item.name"
                :description="item.file_path"
              />
            </a-list-item>
          </template>
        </a-list>
      </a-tab-pane>
    </a-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getProject, getPages, getCases, getScripts, uploadScript } from '../api'

const route = useRoute()
const router = useRouter()
const projectId = route.params.id

const project = ref(null)
const pages = ref([])
const cases = ref([])
const scripts = ref([])
const loading = ref(false)
const activeKey = ref('pages')
const showPageModal = ref(false)
const showCaseModal = ref(false)

const fetchData = async () => {
  loading.value = true
  try {
    const [projectRes, pagesRes, casesRes, scriptsRes] = await Promise.all([
      getProject(projectId),
      getPages(projectId),
      getCases(projectId),
      getScripts(projectId),
    ])
    project.value = projectRes.data
    pages.value = pagesRes.data
    cases.value = casesRes.data
    scripts.value = scriptsRes.data
  } catch (error) {
    console.error('Failed to fetch project data:', error)
  } finally {
    loading.value = false
  }
}

const handleUpload = async ({ file }) => {
  try {
    await uploadScript(projectId, file)
    fetchData()
  } catch (error) {
    console.error('Failed to upload script:', error)
  }
}

const goBack = () => {
  router.push('/projects')
}

onMounted(fetchData)
</script>

<style scoped>
.project-detail {
  padding: 24px;
}
</style>
