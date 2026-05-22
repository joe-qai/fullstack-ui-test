<template>
  <div class="dashboard">
    <a-page-header title="仪表盘" sub-title="UI 自动化测试平台" />
    <a-row :gutter="[16, 16]" style="margin-top: 24px">
      <a-col :span="6">
        <a-card>
          <a-statistic title="项目数" :value="stats.projects" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="用例数" :value="stats.cases" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="设备数" :value="stats.devices">
            <template #suffix>
              <span style="font-size: 14px; color: #999">
                USB {{ stats.devices_usb ?? 0 }} / WiFi {{ stats.devices_wifi ?? 0 }}
              </span>
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="任务数" :value="stats.tasks" />
        </a-card>
      </a-col>
    </a-row>
    <a-row :gutter="[16, 16]" style="margin-top: 24px">
      <a-col :span="12">
        <a-card title="近期任务">
          <a-list :data-source="recentTasks" :loading="loading">
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta :title="item.id" :description="`状态: ${item.status}`" />
              </a-list-item>
            </template>
          </a-list>
        </a-card>
      </a-col>
      <a-col :span="12">
        <a-card title="在线设备">
          <a-list :data-source="onlineDevices" :loading="loading">
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta :title="item.name || item.serial" :description="`平台: ${item.platform}`" />
              </a-list-item>
            </template>
          </a-list>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getStats, getDevices, getTasks } from '../api'

const stats = ref({ projects: 0, cases: 0, devices: 0, devices_usb: 0, devices_wifi: 0, tasks: 0 })
const recentTasks = ref([])
const onlineDevices = ref([])
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const [statsRes, devicesRes, tasksRes] = await Promise.all([
      getStats(),
      getDevices(),
      getTasks(),
    ])
    stats.value = statsRes.data
    recentTasks.value = tasksRes.data.slice(0, 5)
    onlineDevices.value = devicesRes.data.filter(d => d.status === 'online')
  } catch (error) {
    console.error('Failed to fetch dashboard data:', error)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.dashboard {
  padding: 24px;
}
</style>