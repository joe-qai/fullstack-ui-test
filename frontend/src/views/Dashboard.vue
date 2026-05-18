<template>
  <div class="dashboard">
    <a-page-header title="Dashboard" sub-title="UI Automation Test Platform" />

    <a-row :gutter="[16, 16]" style="margin-top: 24px">
      <a-col :span="6">
        <a-card>
          <a-statistic title="Projects" :value="stats.projects" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="Test Cases" :value="stats.cases" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="Devices" :value="stats.devices" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="Tasks" :value="stats.tasks" />
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="[16, 16]" style="margin-top: 24px">
      <a-col :span="12">
        <a-card title="Recent Tasks">
          <a-list :data-source="recentTasks" :loading="loading">
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta
                  :title="item.id"
                  :description="`Status: ${item.status}`"
                />
              </a-list-item>
            </template>
          </a-list>
        </a-card>
      </a-col>
      <a-col :span="12">
        <a-card title="Online Devices">
          <a-list :data-source="onlineDevices" :loading="loading">
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta
                  :title="item.name || item.serial"
                  :description="`Platform: ${item.platform}`"
                />
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
import { getProjects, getDevices, getTasks } from '../api'

const stats = ref({ projects: 0, cases: 0, devices: 0, tasks: 0 })
const recentTasks = ref([])
const onlineDevices = ref([])
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const [projectsRes, devicesRes, tasksRes] = await Promise.all([
      getProjects(),
      getDevices(),
      getTasks(),
    ])
    stats.value.projects = projectsRes.data.length
    stats.value.devices = devicesRes.data.length
    stats.value.tasks = tasksRes.data.length
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
