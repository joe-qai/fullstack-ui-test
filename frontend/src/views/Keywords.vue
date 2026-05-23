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
        <a-tooltip v-if="record.category === 'custom'" title="编辑">
          <a-button type="link" @click="openEditModal(record)">
            <template #icon><EditOutlined /></template>
          </a-button>
        </a-tooltip>
        <a-popconfirm v-if="record.category === 'custom'" title="确定删除?" @confirm="handleDelete(record.id)">
          <a-tooltip title="删除">
            <a-button type="link" danger>
              <template #icon><DeleteOutlined /></template>
            </a-button>
          </a-tooltip>
        </a-popconfirm>
      </template>
    </a-table>

    <a-modal v-model:open="showModal" :title="isEditing ? '编辑自定义关键字' : '创建自定义关键字'" @ok="handleSave" :confirm-loading="saving" style="width: 80vh" centered :body-style="{ maxHeight: '80vh', overflow: 'auto' }">
      <a-form :model="form" layout="vertical">
        <a-form-item label="关键字名称" required>
          <a-input v-model:value="form.name" :disabled="isEditing" placeholder="例如：my_custom_keyword" />
        </a-form-item>
        <a-form-item label="描述" required>
          <a-input v-model:value="form.description" placeholder="请输入关键字描述" />
        </a-form-item>
        <a-form-item label="平台">
          <a-select v-model:value="form.platform">
            <a-select-option value="all">全部</a-select-option>
            <a-select-option value="android">Android</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="Python 代码">
          <div class="code-editor-container">
            <div class="code-hint">
              <a-tag color="blue" size="small">代码提示</a-tag>
              <span class="hint-text">支持完整 Python 语法，函数名应与关键字名称一致</span>
            </div>
            <a-textarea 
              v-model:value="form.code" 
              :rows="12" 
              placeholder="请输入 Python 函数代码"
              class="code-textarea"
            />
            <div class="code-example">
              <a-tag color="green" size="small">示例代码</a-tag>
              <pre class="example-pre">{{ codeExample }}</pre>
            </div>
          </div>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { getKeywords, createCustomKeyword, updateKeyword, deleteKeyword } from '../api'
import { EditOutlined, DeleteOutlined } from '@ant-design/icons-vue'

const keywords = ref([])
const loading = ref(false)
const showModal = ref(false)
const saving = ref(false)
const isEditing = ref(false)
const editingId = ref(null)

const form = ref({ name: '', description: '', platform: 'all', code: '' })

const codeExample = `def my_custom_keyword(d, locator, params=None):
    """
    自定义关键字示例
    :param d: 设备驱动对象
    :param locator: 元素定位器
    :param params: 可选参数（字典类型）
    """
    # 示例：点击元素
    d(resourceId=locator).click()
    
    # 示例：输入文本
    if params and 'text' in params:
        d(resourceId=locator).set_text(params['text'])
    
    return True`

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
  form.value = { 
    name: '', 
    description: '', 
    platform: 'all', 
    code: codeExample.replace('my_custom_keyword', '')
  }
  showModal.value = true
}

const openEditModal = (record) => {
  isEditing.value = true
  editingId.value = record.id
  form.value = { 
    name: record.name, 
    description: record.description || '', 
    platform: record.platform || 'all', 
    code: record.code || '' 
  }
  showModal.value = true
}

const handleSave = async () => {
  if (!form.value.name || !form.value.description) {
    message.warning('请填写必填项')
    return
  }
  if (!form.value.code.trim()) {
    message.warning('请输入 Python 代码')
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

.code-editor-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.code-hint {
  display: flex;
  align-items: center;
  gap: 8px;
}

.hint-text {
  font-size: 12px;
  color: #666;
}

.code-textarea {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.6;
}

.code-example {
  background: #f6f8fa;
  border-radius: 4px;
  padding: 12px;
  margin-top: 8px;
}

.example-pre {
  margin: 8px 0 0 0;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', monospace;
  font-size: 12px;
  line-height: 1.5;
  color: #333;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>