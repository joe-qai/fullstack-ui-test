<template>
  <div class="project-detail">
    <a-page-header
      :title="project?.name || '项目详情'"
      sub-title="管理项目详情"
      @back="goBack"
    />

    <a-tabs v-model:activeKey="activeKey" style="margin-top: 24px">
      <a-tab-pane key="pages" tab="页面">
        <a-button type="primary" @click="showPageModal = true" style="margin-bottom: 16px">
          添加页面
        </a-button>
        <a-list :data-source="pages" row-key="id">
          <template #renderItem="{ item }">
            <a-list-item>
              <a-list-item-meta :title="item.name" :description="item.description" />
            </a-list-item>
          </template>
        </a-list>
      </a-tab-pane>

      <a-tab-pane key="cases" tab="用例">
        <a-button type="primary" @click="showCaseModal = true" style="margin-bottom: 16px">
          添加用例
        </a-button>
        <a-list :data-source="cases" row-key="id">
          <template #renderItem="{ item }">
            <a-list-item>
              <a-list-item-meta :title="item.name" :description="item.type" />
            </a-list-item>
          </template>
        </a-list>
      </a-tab-pane>

      <a-tab-pane key="scripts" tab="脚本">
        <a-upload :custom-request="handleUpload" accept=".py" style="margin-bottom: 16px" :show-upload-list="false">
          <a-button :loading="uploading">上传脚本</a-button>
        </a-upload>
        <a-list :data-source="scripts" row-key="id">
          <template #renderItem="{ item }">
            <a-list-item>
              <a-list-item-meta :title="item.name" :description="item.file_path" />
            </a-list-item>
          </template>
        </a-list>
      </a-tab-pane>
    </a-tabs>

    <!-- 添加页面 Modal -->
    <a-modal v-model:open="showPageModal" title="添加页面" @ok="handleCreatePage">
      <a-form :model="pageForm" layout="vertical">
        <a-form-item label="页面名称" required>
          <a-input v-model:value="pageForm.name" />
        </a-form-item>
        <a-form-item label="描述">
          <a-input v-model:value="pageForm.description" />
        </a-form-item>
        <a-form-item label="所属项目">
          <a-input v-model:value="project?.name" disabled />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 添加用例 Modal -->
    <a-modal v-model:open="showCaseModal" title="添加用例" @ok="handleCreateCase">
      <a-form :model="caseForm" layout="vertical">
        <a-form-item label="用例名称" required>
          <a-input v-model:value="caseForm.name" />
        </a-form-item>
        <a-form-item label="类型">
          <a-select v-model:value="caseForm.type" disabled>
            <a-select-option value="keyword">关键字驱动</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="描述">
          <a-input v-model:value="caseForm.description" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  getProject, getPages, getCases, getScripts,
  uploadScript, createPage, createCase,
} from '../api'

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
const uploading = ref(false)

const pageForm = ref({ name: '', description: '' })
const caseForm = ref({ name: '', type: 'keyword', description: '' })

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
  uploading.value = true
  try {
    await uploadScript(projectId, file)
    message.success('脚本上传成功')
    fetchData()
  } catch (error) {
    message.error('脚本上传失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    uploading.value = false
  }
}

const handleCreatePage = async () => {
  if (!pageForm.value.name) return
  try {
    await createPage(projectId, pageForm.value)
    showPageModal.value = false
    pageForm.value = { name: '', description: '' }
    fetchData()
  } catch (error) {
    message.error('添加页面失败: ' + (error.response?.data?.detail || error.message))
  }
}

const handleCreateCase = async () => {
  if (!caseForm.value.name) return
  try {
    await createCase(projectId, caseForm.value)
    showCaseModal.value = false
    caseForm.value = { name: '', type: 'keyword', description: '' }
    fetchData()
  } catch (error) {
    message.error('添加用例失败: ' + (error.response?.data?.detail || error.message))
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