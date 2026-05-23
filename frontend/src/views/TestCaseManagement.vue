<template>
  <div class="case-management">
    <a-page-header title="用例管理" sub-title="关键字编排 & 用例管理">
      <template #extra>
        <a-select v-model:value="selectedProject" style="width: 200px; margin-right: 12px" placeholder="选择项目" @change="fetchData">
          <a-select-option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</a-select-option>
        </a-select>
        <a-button v-if="selectedRowKeys.length > 0" danger @click="handleBatchDelete">
          批量删除 ({{ selectedRowKeys.length }})
        </a-button>
      </template>
    </a-page-header>

    <!-- 列表模式 -->
    <div v-if="!editingCase">
      <a-table v-if="selectedProject" :columns="caseColumns" :data-source="cases" :loading="loading" row-key="id" style="margin-top: 16px"
        :row-selection="{ selectedRowKeys: selectedRowKeys, onChange: onSelectChange }">
        <template #stepCount="{ record }">{{ record.steps?.length || 0 }}</template>
        <template #dependsOn="{ record }">{{ getDependsName(record.depends_on) }}</template>
        <template #action="{ record }">
          <a-tooltip title="编辑">
            <a-button type="link" @click="startEditCase(record)">
              <template #icon><EditOutlined /></template>
            </a-button>
          </a-tooltip>
          <a-popconfirm title="确定删除?" @confirm="handleDeleteCase(record.id)">
            <a-tooltip title="删除">
              <a-button type="link" danger>
                <template #icon><DeleteOutlined /></template>
              </a-button>
            </a-tooltip>
          </a-popconfirm>
        </template>
      </a-table>
      <a-empty v-else description="请先选择项目" style="margin-top: 48px" />
      <a-button v-if="selectedProject" type="primary" @click="startNewCase" style="margin-top: 16px">
        <PlusOutlined /> 创建用例
      </a-button>
    </div>

    <!-- 编排模式 -->
    <div v-if="editingCase" class="editor-layout">
      <div class="editor-header">
        <a-button @click="cancelEdit">返回列表</a-button>
        <a-button type="primary" @click="saveCase" :loading="saving">保存用例</a-button>
      </div>

      <div class="editor-body">
        <!-- 左栏：关键字库 -->
        <div class="keyword-panel">
          <a-input-search v-model:value="kwSearch" placeholder="搜索关键字" style="margin-bottom: 12px" />
          <a-collapse v-model:activeKey="activeKwCategories" :bordered="false">
            <a-collapse-panel v-for="cat in kwCategories" :key="cat" :header="cat">
              <div v-for="kw in filteredKeywordsByCat(cat)" :key="kw.id" class="kw-item">
                <div class="kw-info">
                  <span class="kw-name">{{ kw.name }}</span>
                  <span class="kw-desc">{{ kw.description }}</span>
                </div>
                <a-button type="primary" size="small" @click="addStepFromKeyword(kw)">
                  <PlusOutlined />
                </a-button>
              </div>
            </a-collapse-panel>
          </a-collapse>
        </div>

        <!-- 右栏：步骤编排区 -->
        <div class="step-panel">
          <a-form layout="vertical" style="margin-bottom: 16px">
            <a-form-item label="用例名称" required>
              <a-input v-model:value="caseForm.name" placeholder="输入用例名称" />
            </a-form-item>
            <a-form-item label="描述">
              <a-input v-model:value="caseForm.description" placeholder="用例描述" />
            </a-form-item>
            <a-form-item label="前置用例（可选）">
              <a-select v-model:value="caseForm.depends_on" placeholder="选择前置用例" allowClear>
                <a-select-option v-for="c in availableDepends" :key="c.id" :value="c.id">{{ c.name }}</a-select-option>
              </a-select>
            </a-form-item>
          </a-form>

          <a-divider>步骤编排</a-divider>

          <div v-for="(step, idx) in caseForm.steps" :key="idx" class="step-row">
            <div class="step-number">{{ idx + 1 }}</div>
            <div class="step-content">
              <a-row :gutter="8">
                <a-col :span="8">
                  <a-select v-model:value="step.keyword_id" placeholder="选择关键字" style="width: 100%" @change="onKeywordChange(step)">
                    <a-select-option v-for="kw in allKeywords" :key="kw.id" :value="kw.id">{{ kw.name }}</a-select-option>
                  </a-select>
                </a-col>
                <a-col :span="6">
          <a-select v-model:value="step.po_element_id" placeholder="选择对象(可选)" style="width: 100%" allowClear>
            <a-select-opt-group v-for="po in pageObjects" :key="po.id" :label="po.name">
              <a-select-option v-for="el in po.elements || []" :key="el.id" :value="el.id">{{ el.name }}</a-select-option>
            </a-select-opt-group>
          </a-select>
        </a-col>
                <a-col :span="8">
                  <div v-if="step.paramFields.length > 0" class="param-inputs">
                    <div v-for="pf in step.paramFields" :key="pf" class="param-field">
                      <a-select v-if="pf === 'package'" v-model:value="step.params[pf]" :placeholder="'选择APK获取包名'" size="small" style="width: 100%" allowClear @change="(val) => { if (!val) step.params[pf] = '' }">
                        <a-select-option v-for="apk in apks" :key="apk.id" :value="apk.package_name || apk.name">
                          {{ apk.file_name || apk.name }} {{ apk.version }} ({{ apk.package_name || '无包名' }})
                        </a-select-option>
                      </a-select>
                      <a-input v-else v-model:value="step.params[pf]" :placeholder="pf" size="small" />
                    </div>
                  </div>
                  <span v-else style="color: #999; font-size: 12px">无参数</span>
                </a-col>
                <a-col :span="2">
                  <a-button size="small" @click="moveStepUp(idx)" :disabled="idx === 0"><ArrowUpOutlined /></a-button>
                </a-col>
                <a-col :span="2">
                  <a-button size="small" @click="moveStepDown(idx)" :disabled="idx === caseForm.steps.length - 1"><ArrowDownOutlined /></a-button>
                </a-col>
                <a-col :span="2">
                  <a-button size="small" danger @click="removeStep(idx)"><DeleteOutlined /></a-button>
                </a-col>
              </a-row>
            </div>
          </div>

          <a-button type="dashed" block @click="addEmptyStep" style="margin-top: 12px">
            <PlusOutlined /> 添加空步骤
          </a-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  PlusOutlined, ArrowUpOutlined, ArrowDownOutlined, DeleteOutlined, EditOutlined,
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import {
  getProjects, getCases, createCase, updateCase, deleteCase,
  getKeywords, getKeywordCategories, getPages, getApks, batchDeleteCases,
} from '../api'

const projects = ref([])
const selectedProject = ref(null)
const cases = ref([])
const loading = ref(false)
const saving = ref(false)
const selectedRowKeys = ref([])

// 编排模式状态
const editingCase = ref(false)
const editingCaseId = ref(null) // null=新建, 有值=编辑
const caseForm = ref({
  name: '', type: 'keyword', description: '', depends_on: null,
  steps: [],
})

// 关键字数据
const allKeywords = ref([])
const kwCategories = ref([])
const kwSearch = ref('')
const activeKwCategories = ref([])

// PO + 元素数据（用于编排选元素）
const pageObjects = ref([])

const apks = ref([])

const getApkPackageName = (apkId) => {
  const apk = apks.value.find(a => a.id === apkId)
  return apk ? (apk.package_name || apk.name) : ''
}

const caseColumns = [
  { title: '用例名称', dataIndex: 'name', key: 'name' },
  { title: '前置用例', key: 'dependsOn', slots: { customRender: 'dependsOn' } },
  { title: '步骤数', key: 'stepCount', slots: { customRender: 'stepCount' } },
  { title: '操作', key: 'action', slots: { customRender: 'action' } },
]

const onSelectChange = (keys) => { selectedRowKeys.value = keys }

const availableDepends = computed(() => {
  return cases.value.filter(c => c.id !== editingCaseId.value)
})

const getProjectName = (projectId) => {
  const p = projects.value.find(p => p.id === projectId)
  return p ? p.name : projectId
}

const filteredKeywordsByCat = (cat) => {
  const kws = allKeywords.value.filter(kw => kw.category === cat)
  if (!kwSearch.value) return kws
  return kws.filter(kw => kw.name.includes(kwSearch.value) || kw.description?.includes(kwSearch.value))
}

const getDependsName = (dependsId) => {
  if (!dependsId) return '无'
  const c = cases.value.find(c => c.id === dependsId)
  return c ? c.name : dependsId
}

const parseKeywordParams = (kw) => {
  try {
    const p = typeof kw.params === 'string' ? JSON.parse(kw.params) : kw.params
    if (p && p.properties) return Object.keys(p.properties)
    return []
  } catch {
    return []
  }
}

const fetchData = async () => {
  if (!selectedProject.value) return
  loading.value = true
  try {
    const [caseRes, kwRes, catRes, pageRes, apkRes] = await Promise.all([
      getCases(selectedProject.value),
      getKeywords(),
      getKeywordCategories(),
      getPages(selectedProject.value),
      getApks(),
    ])
    cases.value = caseRes.data
    allKeywords.value = kwRes.data
    
    // 按 basic、platform、assertion 排序
    const priorityOrder = ['basic', 'platform', 'assertion']
    kwCategories.value = catRes.data
      .map(c => c.category)
      .sort((a, b) => {
        const idxA = priorityOrder.indexOf(a)
        const idxB = priorityOrder.indexOf(b)
        if (idxA !== -1 && idxB !== -1) return idxA - idxB
        if (idxA !== -1) return -1
        if (idxB !== -1) return 1
        return a.localeCompare(b)
      })
    pageObjects.value = pageRes.data
    apks.value = apkRes.data
    activeKwCategories.value = [...kwCategories.value]
  } catch (error) {
    console.error('Failed to fetch data:', error)
  } finally {
    loading.value = false
  }
}

const startNewCase = () => {
  editingCaseId.value = null
  caseForm.value = { name: '', type: 'keyword', description: '', depends_on: null, steps: [] }
  editingCase.value = true
}

const startEditCase = (record) => {
  editingCaseId.value = record.id
  caseForm.value = {
    name: record.name,
    type: record.type,
    description: record.description || '',
    depends_on: record.depends_on || null,
    steps: (record.steps || []).map(s => {
      const kw = allKeywords.value.find(k => k.id === s.keyword_id)
      const parsedParams = typeof s.params === 'string' ? JSON.parse(s.params || '{}') : (s.params || {})
      const paramFields = kw ? parseKeywordParams(kw) : []
      return {
        keyword_id: s.keyword_id,
        po_element_id: s.po_element_id || null,
        params: { ...parsedParams },
        paramFields,
        step_order: s.step_order,
      }
    }),
  }
  editingCase.value = true
}

const cancelEdit = () => {
  editingCase.value = false
  editingCaseId.value = null
}

const addStepFromKeyword = (kw) => {
  const paramFields = parseKeywordParams(kw)
  const params = {}
  paramFields.forEach(f => { params[f] = '' })
  caseForm.value.steps.push({
    keyword_id: kw.id,
    po_element_id: null,
    params,
    paramFields,
    step_order: caseForm.value.steps.length + 1,
  })
}

const addEmptyStep = () => {
  caseForm.value.steps.push({
    keyword_id: null,
    po_element_id: null,
    params: {},
    paramFields: [],
    step_order: caseForm.value.steps.length + 1,
  })
}

const onKeywordChange = (step) => {
  const kw = allKeywords.value.find(k => k.id === step.keyword_id)
  if (kw) {
    step.paramFields = parseKeywordParams(kw)
    step.params = {}
    step.paramFields.forEach(f => { step.params[f] = '' })
  } else {
    step.paramFields = []
    step.params = {}
  }
}

const moveStepUp = (idx) => {
  if (idx === 0) return
  const steps = caseForm.value.steps
  const item = steps.splice(idx, 1)[0]
  steps.splice(idx - 1, 0, item)
  steps.forEach((s, i) => { s.step_order = i + 1 })
}

const moveStepDown = (idx) => {
  const steps = caseForm.value.steps
  if (idx === steps.length - 1) return
  const item = steps.splice(idx, 1)[0]
  steps.splice(idx + 1, 0, item)
  steps.forEach((s, i) => { s.step_order = i + 1 })
}

const removeStep = (idx) => {
  caseForm.value.steps.splice(idx, 1)
  caseForm.value.steps.forEach((s, i) => { s.step_order = i + 1 })
}

const saveCase = async () => {
  if (!caseForm.value.name) {
    alert('请输入用例名称')
    return
  }
  saving.value = true
  try {
    const payload = {
      name: caseForm.value.name,
      type: caseForm.value.type,
      description: caseForm.value.description,
      depends_on: caseForm.value.depends_on,
      steps: caseForm.value.steps
        .filter(s => s.keyword_id) // 忽略空步骤
        .map(s => ({
          keyword_id: s.keyword_id,
          po_element_id: s.po_element_id,
          params: s.params,
          step_order: s.step_order,
        })),
    }
    if (editingCaseId.value) {
      await updateCase(selectedProject.value, editingCaseId.value, payload)
    } else {
      await createCase(selectedProject.value, payload)
    }
    editingCase.value = false
    editingCaseId.value = null
    fetchData()
  } catch (error) {
    console.error('Failed to save case:', error)
    alert('保存失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    saving.value = false
  }
}

const handleDeleteCase = async (caseId) => {
  try {
    await deleteCase(selectedProject.value, caseId)
    fetchData()
  } catch (error) {
    console.error('Failed to delete case:', error)
  }
}

const handleBatchDelete = async () => {
  const ids = selectedRowKeys.value
  if (ids.length === 0) return
  try {
    const res = await batchDeleteCases(selectedProject.value, ids)
    message.success(`成功删除 ${res.data.count} 个用例`)
    selectedRowKeys.value = []
    fetchData()
  } catch (error) {
    message.error('批量删除失败: ' + (error.response?.data?.detail || error.message))
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
.case-management { padding: 24px; }

.editor-layout {
  margin-top: 16px;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}

.editor-body {
  display: flex;
  gap: 16px;
}

.keyword-panel {
  width: 280px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  padding: 12px;
  background: #fafafa;
  overflow-y: auto;
  max-height: 600px;
}

.kw-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid #f0f0f0;
}

.kw-info {
  flex: 1;
}

.kw-name {
  font-weight: 500;
  margin-right: 8px;
}

.kw-desc {
  color: #999;
  font-size: 12px;
}

.step-panel {
  flex: 1;
  min-width: 0;
}

.step-row {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  padding: 8px;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  background: #fff;
}

.step-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #1890ff;
  color: #fff;
  text-align: center;
  line-height: 32px;
  font-weight: bold;
  margin-right: 12px;
  flex-shrink: 0;
}

.step-content {
  flex: 1;
  min-width: 0;
}

.param-inputs {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.param-field {
  flex: 1;
  min-width: 80px;
}
</style>