<template>
  <div class="keywords">
    <a-page-header
      title="Keywords"
      sub-title="Built-in and custom keywords"
    />

    <a-table
      :columns="columns"
      :data-source="keywords"
      :loading="loading"
      row-key="id"
      style="margin-top: 24px"
    >
      <template #category="{ record }">
        <a-tag :color="getCategoryColor(record.category)">
          {{ record.category }}
        </a-tag>
      </template>
    </a-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getKeywords } from '../api'

const keywords = ref([])
const loading = ref(false)

const columns = [
  { title: 'Name', dataIndex: 'name', key: 'name' },
  { title: 'Category', dataIndex: 'category', key: 'category', slots: { customRender: 'category' } },
  { title: 'Platform', dataIndex: 'platform', key: 'platform' },
  { title: 'Description', dataIndex: 'description', key: 'description' },
]

const getCategoryColor = (category) => {
  const colors = {
    basic: 'green',
    platform: 'blue',
    custom: 'orange',
  }
  return colors[category] || 'default'
}

const fetchKeywords = async () => {
  loading.value = true
  try {
    const res = await getKeywords()
    keywords.value = res.data
  } catch (error) {
    console.error('Failed to fetch keywords:', error)
  } finally {
    loading.value = false
  }
}

onMounted(fetchKeywords)
</script>

<style scoped>
.keywords {
  padding: 24px;
}
</style>
