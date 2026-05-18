<template>
  <div class="devices">
    <a-page-header
      title="Devices"
      sub-title="Manage connected devices"
    >
      <template #extra>
        <a-button type="primary" @click="handleScan">Scan Devices</a-button>
      </template>
    </a-page-header>

    <a-table
      :columns="columns"
      :data-source="devices"
      :loading="loading"
      row-key="id"
      style="margin-top: 24px"
    >
      <template #status="{ record }">
        <a-tag :color="record.status === 'online' ? 'green' : 'red'">
          {{ record.status }}
        </a-tag>
      </template>
    </a-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getDevices, scanDevices } from '../api'

const devices = ref([])
const loading = ref(false)

const columns = [
  { title: 'Name', dataIndex: 'name', key: 'name' },
  { title: 'Serial', dataIndex: 'serial', key: 'serial' },
  { title: 'Platform', dataIndex: 'platform', key: 'platform' },
  { title: 'Status', dataIndex: 'status', key: 'status', slots: { customRender: 'status' } },
]

const fetchDevices = async () => {
  loading.value = true
  try {
    const res = await getDevices()
    devices.value = res.data
  } catch (error) {
    console.error('Failed to fetch devices:', error)
  } finally {
    loading.value = false
  }
}

const handleScan = async () => {
  loading.value = true
  try {
    await scanDevices()
    await fetchDevices()
  } catch (error) {
    console.error('Failed to scan devices:', error)
  } finally {
    loading.value = false
  }
}

onMounted(fetchDevices)
</script>

<style scoped>
.devices {
  padding: 24px;
}
</style>
