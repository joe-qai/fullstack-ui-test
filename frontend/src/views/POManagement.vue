<template>
  <div class="po-management">
    <a-page-header title="PO管理" sub-title="Page Object & 元素管理">
      <template #extra>
        <a-select v-model:value="selectedProject" style="width: 200px" placeholder="选择项目" @change="fetchData">
          <a-select-option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</a-select-option>
        </a-select>
      </template>
    </a-page-header>

    <a-table v-if="selectedProject" :columns="poColumns" :data-source="pages" :loading="loading" row-key="id" style="margin-top: 16px"
      :expandable="{ expandedRowRender: renderElements }">
      <template #action="{ record }">
        <a-button type="link" @click="showElementModal(record)">添加元素</a-button>
        <a-popconfirm title="确定删除?" @confirm="handleDeletePage(record.id)">
          <a-button type="link" danger>删除</a-button>
        </a-popconfirm>
      </template>
    </a-table>
    <a-empty v-else description="请先选择项目" style="margin-top: 48px" />

    <a-button v-if="selectedProject" type="primary" @click="showPageModal = true" style="margin-top: 16px">创建 Page Object</a-button>

    <a-modal v-model:open="showPageModal" title="创建 Page Object" @ok="handleCreatePage">
      <a-form :model="pageForm" layout="vertical">
        <a-form-item label="页面名称" required>
          <a-input v-model:value="pageForm.name" />
        </a-form-item>
        <a-form-item label="描述">
          <a-input v-model:value="pageForm.description" />
        </a-form-item>
        <a-form-item label="所属项目">
          <span style="color: #666">{{ selectedProjectName }}</span>
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal v-model:open="showElementModalFlag" title="添加元素" @ok="handleCreateElement">
      <a-form :model="elementForm" layout="vertical">
        <a-form-item label="元素名称" required>
          <a-input v-model:value="elementForm.name" />
        </a-form-item>
        <a-form-item label="定位方式" required>
          <a-select v-model:value="elementForm.locator_type">
            <a-select-option value="id">id</a-select-option>
            <a-select-option value="xpath">xpath</a-select-option>
            <a-select-option value="class name">class name</a-select-option>
            <a-select-option value="accessibility_id">accessibility_id</a-select-option>
            <a-select-option value="text">text</a-select-option>
            <a-select-option value="uiautomator">uiautomator</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="定位值" required>
          <a-input v-model:value="elementForm.locator_value" />
        </a-form-item>
        <a-form-item label="描述">
          <a-input v-model:value="elementForm.description" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted, h, computed } from 'vue'
import { getProjects, getPages, createPage, deletePage, createElement, deleteElement } from '../api'

const projects = ref([])
const selectedProject = ref(null)
const pages = ref([])
const loading = ref(false)
const showPageModal = ref(false)
const showElementModalFlag = ref(false)
const currentPageId = ref(null)

const selectedProjectName = computed(() => {
  const p = projects.value.find(p => p.id === selectedProject.value)
  return p ? p.name : ''
})

const pageForm = ref({ name: '', description: '' })
const elementForm = ref({ name: '', locator_type: 'id', locator_value: '', description: '' })

const poColumns = [
  { title: '页面名称', dataIndex: 'name', key: 'name' },
  { title: '描述', dataIndex: 'description', key: 'description' },
  { title: '元素数', key: 'elements', customRender: ({ record }) => record.elements?.length || 0 },
  { title: '操作', key: 'action', slots: { customRender: 'action' } },
]

const renderElements = ({ record }) => {
  const elements = record.elements || []
  if (elements.length === 0) return h('span', { style: { color: '#999' } }, '暂无元素')
  const columns = [
    { title: '元素名', dataIndex: 'name' },
    { title: '定位方式', dataIndex: 'locator_type' },
    { title: '定位值', dataIndex: 'locator_value' },
    { title: '操作', key: 'action', customRender: ({ record: el }) => h('a-popconfirm', { title: '确定删除?', onConfirm: () => handleDeleteElement(record.id, el.id) }, () => h('a-button', { type: 'link', danger: true }, '删除')) },
  ]
  return h('a-table', { columns, dataSource: elements, rowKey: 'id', size: 'small', pagination: false })
}

const fetchData = async () => {
  if (!selectedProject.value) return
  loading.value = true
  try {
    const res = await getPages(selectedProject.value)
    pages.value = res.data
  } catch (error) {
    console.error('Failed to fetch pages:', error)
  } finally {
    loading.value = false
  }
}

const handleCreatePage = async () => {
  try {
    await createPage(selectedProject.value, pageForm.value)
    showPageModal.value = false
    pageForm.value = { name: '', description: '' }
    fetchData()
  } catch (error) {
    console.error('Failed to create page:', error)
  }
}

const handleDeletePage = async (pageId) => {
  try {
    await deletePage(selectedProject.value, pageId)
    fetchData()
  } catch (error) {
    console.error('Failed to delete page:', error)
  }
}

const showElementModal = (pageRecord) => {
  currentPageId.value = pageRecord.id
  elementForm.value = { name: '', locator_type: 'id', locator_value: '', description: '' }
  showElementModalFlag.value = true
}

const handleCreateElement = async () => {
  try {
    await createElement(selectedProject.value, currentPageId.value, elementForm.value)
    showElementModalFlag.value = false
    fetchData()
  } catch (error) {
    console.error('Failed to create element:', error)
  }
}

const handleDeleteElement = async (pageId, elementId) => {
  try {
    await deleteElement(selectedProject.value, pageId, elementId)
    fetchData()
  } catch (error) {
    console.error('Failed to delete element:', error)
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
.po-management { padding: 24px; }
</style>