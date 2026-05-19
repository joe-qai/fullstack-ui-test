<template>
  <div class="keywords">
    <a-page-header title="关键字管理" sub-title="内置关键字和自定义关键字">
      <template #extra>
        <a-button type="primary" @click="openCreateModal">创建自定义关键字</a-button>
      </template>
    </a-page-header>

    <a-table :columns="columns" :data-source="keywords" :loading="loading" row-key="id" style="margin-top: 24px">
      <template #category="{ record }">
        <a-tag :color="getCategoryColor(record.category)">{{ record.category }}</a-tag>
      </template>
      <template #action="{ record }">
        <a-button v-if="record.category === 'custom'" type="link" @click="openEditModal(record)">编辑</a-button>
        <a-popconfirm v-if="record.category === 'custom'" title="确定删除?" @confirm="handleDelete(record.id)">
          <a-button type="link" danger>删除</a-button>
        </a-popconfirm>
      </template>
    </a-table>

    <a-modal v-model:open="showModal" :title="isEditing ? '编辑自定义关键字' : '创建自定义关键字'" @ok="handleSave" :confirm-loading="saving" width="700">
      <a-form :model="form" layout="vertical">
        <a-form-item label="关键字名称" required>
          <a-input v-model:value="form.name" :disabled="isEditing" />
        </a-form-item>
        <a-form-item label="描述" required>
          <a-input v-model:value="form.description" />
        </a-form-item>
        <a-form-item label="平台">
          <a-select v-model:value="form.platform">
            <a-select-option value="all">全部</a-select-option>
            <a-select-option value="android">Android</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="Python 代码">
          <a-textarea v-model:value="form.code" :rows="8" placeholder="def your_keyword(d, locator, params): ..." />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { getKeywords, createCustomKeyword, updateKeyword, deleteKeyword } from '../api'

const keywords = ref([])
const loading = ref(false)
const showModal = ref(false)
const saving = ref(false)
const isEditing = ref(false)
const editingId = ref(null)

const form = ref({ name: '', description: '', platform: 'all', code: '' })

const columns = [
  { title: '关键字名称', dataIndex: 'name', key: 'name' },
  { title: '分类', dataIndex: 'category', key: 'category', slots: { customRender: 'category' } },
  { title: '平台', dataIndex: 'platform', key: 'platform' },
  { title: '描述', dataIndex: 'description', key: 'description' },
  { title: '操作', key: 'action', slots: { customRender: 'action' } },
]

const getCategoryColor = (category) => {
  const colors = { basic: 'green', platform: 'blue', custom: 'orange' }
  return colors[category] || 'default'
}

const fetchKeywords = async () => {
  loading.value = true
  try {
    const res = await getKeywords()
    keywords.value = res.data
  } catch (error) {
    message.error('获取关键字失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

const openCreateModal = () => {
  isEditing.value = false
  editingId.value = null
  form.value = { name: '', description: '', platform: 'all', code: '' }
  showModal.value = true
}

const openEditModal = (record) => {
  isEditing.value = true
  editingId.value = record.id
  form.value = { name: record.name, description: record.description || '', platform: record.platform || 'all', code: record.code || '' }
  showModal.value = true
}

const handleSave = async () => {
  if (!form.value.name || !form.value.description) {
    message.warning('请填写必填项')
    return
  }
  saving.value = true
  try {
    if (isEditing.value) {
      await updateKeyword(editingId.value, form.value)
      message.success('关键字更新成功')
    } else {
      await createCustomKeyword('default', form.value)
      message.success('关键字创建成功')
    }
    showModal.value = false
    fetchKeywords()
  } catch (error) {
    message.error('保存失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    saving.value = false
  }
}

const handleDelete = async (id) => {
  try {
    await deleteKeyword(id)
    message.success('关键字删除成功')
    fetchKeywords()
  } catch (error) {
    message.error('删除失败: ' + (error.response?.data?.detail || error.message))
  }
}

onMounted(fetchKeywords)
</script>

<style scoped>
.keywords { padding: 24px; }
</style>