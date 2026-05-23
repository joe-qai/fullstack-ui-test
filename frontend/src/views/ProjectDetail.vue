<template>
  <div class="project-detail">
    <a-page-header
      :title="project?.name || '项目详情'"
      :sub-title="project?.description || ''"
      @back="goBack"
    />

    <a-spin :spinning="loading">
      <a-row :gutter="16" style="margin-top: 24px">
        <a-col :span="8">
          <a-card title="页面 (PO)" :bordered="false" hoverable @click="navigateTo('pages')">
            <a-statistic :value="pages.length" suffix="个" />
            <template #extra><a-button type="link">前往管理 →</a-button></template>
          </a-card>
        </a-col>
        <a-col :span="8">
          <a-card title="用例管理" :bordered="false" hoverable @click="navigateTo('cases')">
            <a-statistic :value="cases.length" suffix="个" />
            <template #extra><a-button type="link">前往管理 →</a-button></template>
          </a-card>
        </a-col>
        <a-col :span="8">
          <a-card title="脚本" :bordered="false" hoverable @click="navigateTo('scripts')">
            <a-statistic :value="scripts.length" suffix="个" />
            <template #extra><a-button type="link">前往管理 →</a-button></template>
          </a-card>
        </a-col>
      </a-row>

      <a-card title="项目信息" style="margin-top: 16px" :bordered="false">
        <a-descriptions :column="2">
          <a-descriptions-item label="项目名称">{{ project?.name }}</a-descriptions-item>
          <a-descriptions-item label="平台">{{ project?.platform }}</a-descriptions-item>
          <a-descriptions-item label="描述" :span="2">{{ project?.description || '无' }}</a-descriptions-item>
          <a-descriptions-item label="创建时间">{{ formatDate(project?.created_at) }}</a-descriptions-item>
        </a-descriptions>
      </a-card>
    </a-spin>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getProject, getPages, getCases, getScripts } from '../api'
import { formatDate } from '../utils/format'

const route = useRoute()
const router = useRouter()
const projectId = route.params.id

const project = ref(null)
const pages = ref([])
const cases = ref([])
const scripts = ref([])
const loading = ref(false)

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

const navigateTo = (section) => {
  const routeMap = { pages: '/po', cases: '/cases', scripts: '/scripts' }
  router.push(routeMap[section] || '/')
}

const goBack = () => {
  router.push('/projects')
}

onMounted(fetchData)
</script>

<style scoped>
.project-detail { padding: 24px; }
</style>
