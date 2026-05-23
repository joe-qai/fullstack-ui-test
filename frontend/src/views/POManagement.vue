<template>
  <div class="po-management">
    <a-page-header title="对象管理" sub-title="Page Object & 元素管理">
      <template #extra>
        <a-select v-model:value="selectedProject" style="width: 200px" placeholder="选择项目" @change="fetchData">
          <a-select-option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</a-select-option>
        </a-select>
      </template>
    </a-page-header>

    <a-table v-if="selectedProject" :columns="poColumns" :data-source="pages" :loading="loading" row-key="id" style="margin-top: 16px"
      :expandable="{ expandedRowRender: renderElements }">
      <template #action="{ record }">
        <a-tooltip title="编辑">
          <a-button type="link" @click="openEditPageModal(record)">
            <template #icon><EditOutlined /></template>
          </a-button>
        </a-tooltip>
        <a-tooltip title="跨项目复制">
          <a-button type="link" @click="showCopyModal(record)">
            <template #icon><CopyOutlined /></template>
          </a-button>
        </a-tooltip>
        <a-popconfirm title="确定删除?" @confirm="handleDeletePage(record.id)">
          <a-tooltip title="删除">
            <a-button type="link" danger>
              <template #icon><DeleteOutlined /></template>
            </a-button>
          </a-tooltip>
        </a-popconfirm>
      </template>
    </a-table>
    <a-empty v-else description="请先选择项目" style="margin-top: 48px" />

    <a-button v-if="selectedProject" type="primary" @click="openCreatePageModal" style="margin-top: 16px">创建 Page Object</a-button>

    <!-- 创建页面弹窗 -->
    <a-modal v-model:open="showCreateModal" title="创建页面对象" @ok="handleCreatePage" :width="600">
      <a-form :model="pageForm" layout="vertical">
        <a-form-item label="页面名称" required>
          <a-input v-model:value="pageForm.name" placeholder="输入页面名称" />
        </a-form-item>
        <a-form-item label="描述">
          <a-input v-model:value="pageForm.description" placeholder="输入页面描述" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 编辑页面+元素管理弹窗 -->
    <a-modal v-model:open="showEditModal" :title="'编辑页面对象: ' + editingPageName" @ok="handleSavePage" :width="900">
      <a-form layout="vertical">
        <a-divider orientation="left">页面信息</a-divider>
        <a-row :gutter="12">
          <a-col :span="12">
            <a-form-item label="页面名称" required>
              <a-input v-model:value="pageForm.name" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="描述">
              <a-input v-model:value="pageForm.description" />
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>

      <a-divider orientation="left">对象管理 ({{ pageElements.length }} 个对象)</a-divider>

      <a-table :columns="elementColumns" :data-source="pageElements" row-key="id" size="small"
        :pagination="{ pageSize: 5 }" :loading="elementsLoading">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'name'">
            <a-input v-model:value="record.name" size="small" style="width: 120px" />
          </template>
          <template v-else-if="column.key === 'locator_type'">
            <a-select v-model:value="record.locator_type" size="small" style="width: 140px">
              <a-select-option value="text">text</a-select-option>
              <a-select-option value="textContains">textContains</a-select-option>
              <a-select-option value="resourceId">resourceId</a-select-option>
              <a-select-option value="xpath">xpath</a-select-option>
              <a-select-option value="className">className</a-select-option>
              <a-select-option value="description">description</a-select-option>
              <a-select-option value="descriptionContains">descriptionContains</a-select-option>
            </a-select>
          </template>
          <template v-else-if="column.key === 'locator_value'">
            <a-input v-model:value="record.locator_value" size="small" style="width: 200px" />
          </template>
          <template v-else-if="column.key === 'description'">
            <a-input v-model:value="record.description" size="small" style="width: 120px" />
          </template>
          <template v-else-if="column.key === 'action'">
            <a-button type="link" danger size="small" @click="removeElement(record.id)">删除</a-button>
          </template>
        </template>
      </a-table>

      <a-divider>添加新对象</a-divider>
      <a-row :gutter="8" align="middle">
        <a-col :span="4">
          <a-input v-model:value="newElement.name" placeholder="对象名" size="small" />
        </a-col>
        <a-col :span="5">
          <a-select v-model:value="newElement.locator_type" placeholder="定位方式" size="small" style="width: 100%">
            <a-select-option value="text">text</a-select-option>
            <a-select-option value="textContains">textContains</a-select-option>
            <a-select-option value="resourceId">resourceId</a-select-option>
            <a-select-option value="xpath">xpath</a-select-option>
            <a-select-option value="className">className</a-select-option>
            <a-select-option value="description">description</a-select-option>
            <a-select-option value="descriptionContains">descriptionContains</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="8">
          <a-input v-model:value="newElement.locator_value" placeholder="定位值" size="small" />
        </a-col>
        <a-col :span="5">
          <a-input v-model:value="newElement.description" placeholder="描述" size="small" />
        </a-col>
        <a-col :span="2">
          <a-button type="primary" size="small" @click="addElement">添加</a-button>
        </a-col>
      </a-row>
    </a-modal>

    <a-modal v-model:open="showCopyModalFlag" title="跨项目复制 PO" @ok="handleCopyPage">
      <a-form layout="vertical">
        <a-form-item label="源页面">
          <span style="color: #666">{{ copySourcePage?.name }}</span>
        </a-form-item>
        <a-form-item label="目标项目" required>
          <a-select v-model:value="copyTargetProject" placeholder="选择目标项目">
            <a-select-option v-for="p in otherProjects" :key="p.id" :value="p.id">{{ p.name }}</a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, h } from 'vue'
import { message } from 'ant-design-vue'
import { getProjects, getPages, createPage, deletePage, createElement, deleteElement, copyPage, updateElement, updatePage, getElements } from '../api'
import { EditOutlined, CopyOutlined, DeleteOutlined } from '@ant-design/icons-vue'

const projects = ref([])
const selectedProject = ref(null)
const pages = ref([])
const loading = ref(false)
const showCreateModal = ref(false)
const showEditModal = ref(false)
const showCopyModalFlag = ref(false)
const currentPageId = ref(null)
const editingPageName = ref('')
const copySourcePage = ref(null)
const copyTargetProject = ref(null)

const pageForm = ref({ name: '', description: '' })
const pageElements = ref([])
const elementsLoading = ref(false)
const newElement = ref({ name: '', locator_type: 'text', locator_value: '', description: '' })

const otherProjects = computed(() => {
  return projects.value.filter(p => p.id !== selectedProject.value)
})

const poColumns = [
  { title: '页面名称', dataIndex: 'name', key: 'name' },
  { title: '对象数', key: 'elements', customRender: ({ record }) => record.elements?.length || 0 },
  { title: '描述', dataIndex: 'description', key: 'description' },
  { title: '操作', key: 'action', slots: { customRender: 'action' } },
]

const elementColumns = [
  { title: '对象名', key: 'name', width: 140 },
  { title: '定位方式', key: 'locator_type', width: 150 },
  { title: '定位值', key: 'locator_value', width: 210 },
  { title: '描述', key: 'description', width: 130 },
  { title: '操作', key: 'action', width: 80 },
]

const renderElements = ({ record }) => {
  const elements = record.elements || []
  if (elements.length === 0) return h('span', { style: { color: '#999' } }, '暂无对象')
  const columns = [
    { title: '对象名', dataIndex: 'name' },
    { title: '定位方式', dataIndex: 'locator_type' },
    { title: '定位值', dataIndex: 'locator_value' },
    { title: '描述', dataIndex: 'description' },
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

const openCreatePageModal = () => {
  pageForm.value = { name: '', description: '' }
  showCreateModal.value = true
}

const openEditPageModal = async (record) => {
  currentPageId.value = record.id
  editingPageName.value = record.name
  pageForm.value = { name: record.name, description: record.description || '' }
  elementsLoading.value = true
  showEditModal.value = true
  try {
    const res = await getElements(selectedProject.value, record.id)
    pageElements.value = res.data
  } catch (error) {
    console.error('Failed to fetch elements:', error)
    pageElements.value = record.elements || []
  } finally {
    elementsLoading.value = false
  }
}

const handleCreatePage = async () => {
  if (!pageForm.value.name) {
    message.warning('请输入页面名称')
    return
  }
  try {
    await createPage(selectedProject.value, pageForm.value)
    showCreateModal.value = false
    fetchData()
    message.success('创建成功')
  } catch (error) {
    console.error('Failed to create page:', error)
  }
}

const handleSavePage = async () => {
  if (!pageForm.value.name) {
    message.warning('请输入页面名称')
    return
  }
  try {
    await updatePage(selectedProject.value, currentPageId.value, pageForm.value)
    
    for (const el of pageElements.value) {
      if (el.id) {
        await updateElement(selectedProject.value, currentPageId.value, el.id, {
          name: el.name,
          locator_type: el.locator_type,
          locator_value: el.locator_value,
          description: el.description,
        })
      }
    }
    
    showEditModal.value = false
    fetchData()
    message.success('保存成功')
  } catch (error) {
    console.error('Failed to save page:', error)
  }
}

const addElement = async () => {
  if (!newElement.value.name || !newElement.value.locator_value) {
    message.warning('请填写对象名称和定位值')
    return
  }
  try {
    await createElement(selectedProject.value, currentPageId.value, { ...newElement.value })
    const res = await getElements(selectedProject.value, currentPageId.value)
    pageElements.value = res.data
    newElement.value = { name: '', locator_type: 'text', locator_value: '', description: '' }
    message.success('添加成功')
  } catch (error) {
    console.error('Failed to add element:', error)
  }
}

const removeElement = async (elementId) => {
  try {
    await deleteElement(selectedProject.value, currentPageId.value, elementId)
    pageElements.value = pageElements.value.filter(el => el.id !== elementId)
    message.success('删除成功')
  } catch (error) {
    console.error('Failed to remove element:', error)
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

const showCopyModal = (pageRecord) => {
  copySourcePage.value = pageRecord
  copyTargetProject.value = null
  showCopyModalFlag.value = true
}

const handleCopyPage = async () => {
  if (!copyTargetProject.value) {
    message.warning('请选择目标项目')
    return
  }
  try {
    await copyPage(copyTargetProject.value, copySourcePage.value.id)
    showCopyModalFlag.value = false
    message.success('复制成功')
  } catch (error) {
    message.error('复制失败: ' + (error.response?.data?.detail || error.message))
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
