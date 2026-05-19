<template>
  <div class="debug">
    <a-page-header title="调试" sub-title="使用 uiautodev 调试设备" />

    <a-row :gutter="[16, 16]" style="margin-top: 24px">
      <a-col :span="24">
        <a-card title="uiautodev 状态">
          <a-descriptions :column="2">
            <a-descriptions-item label="状态">
              <a-tag :color="uiautodevStatus.running ? 'green' : 'red'">
                {{ uiautodevStatus.running ? '运行中' : '已停止' }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="URL">
              <a :href="uiautodevStatus.url" target="_blank">{{ uiautodevStatus.url }}</a>
            </a-descriptions-item>
            <a-descriptions-item label="主机">{{ uiautodevStatus.host }}</a-descriptions-item>
            <a-descriptions-item label="端口">{{ uiautodevStatus.port }}</a-descriptions-item>
          </a-descriptions>
          <a-space>
            <a-button type="primary" @click="startUiautodev">启动</a-button>
            <a-button danger @click="stopUiautodev">停止</a-button>
          </a-space>
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="[16, 16]" style="margin-top: 24px">
      <a-col :span="24">
        <a-card title="设备检查器">
          <a-select v-model:value="selectedDevice" placeholder="选择设备" style="width: 300px; margin-bottom: 16px" @change="handleDeviceChange">
            <a-select-option v-for="device in devices" :key="device.id" :value="device.serial">
              {{ device.name || device.serial }}
            </a-select-option>
          </a-select>
          <div v-if="selectedDevice">
            <a-alert v-if="iframeError" :message="iframeError" type="error" show-icon style="margin-bottom: 12px" />
            <div v-if="!uiautodevStatus.running" class="iframe-container">
              <a-alert message="uiautodev 未运行，请先启动" type="warning" />
            </div>
            <div v-else class="iframe-container">
              <iframe :src="iframeUrl" width="100%" height="800" frameborder="0" @error="iframeError = 'iframe 加载失败'" />
            </div>
          </div>
          <a-empty v-else description="请选择设备开始调试" />
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { getDevices } from '../api'

const devices = ref([])
const selectedDevice = ref(null)
const iframeUrl = ref('')
const iframeError = ref('')
const uiautodevStatus = ref({ running: false, url: '', host: '', port: 0 })

const fetchDevices = async () => {
  try {
    const res = await getDevices()
    devices.value = res.data
  } catch (error) {
    console.error('Failed to fetch devices:', error)
  }
}

const fetchUiautodevStatus = async () => {
  try {
    const res = await axios.get('/api/debug/uiautodev/status')
    uiautodevStatus.value = res.data
  } catch (error) {
    console.error('Failed to fetch uiautodev status:', error)
  }
}

const startUiautodev = async () => {
  try {
    await axios.post('/api/debug/uiautodev/start')
    await fetchUiautodevStatus()
  } catch (error) {
    console.error('Failed to start uiautodev:', error)
  }
}

const stopUiautodev = async () => {
  try {
    await axios.post('/api/debug/uiautodev/stop')
    await fetchUiautodevStatus()
  } catch (error) {
    console.error('Failed to stop uiautodev:', error)
  }
}

const handleDeviceChange = async (serial) => {
  iframeError.value = ''
  try {
    const res = await axios.get(`/api/debug/uiautodev/device/${serial}`)
    iframeUrl.value = res.data.url
  } catch (error) {
    iframeError.value = '获取设备调试 URL 失败: ' + (error.response?.data?.detail || error.message)
  }
}

onMounted(() => {
  fetchDevices()
  fetchUiautodevStatus()
})
</script>

<style scoped>
.debug { padding: 24px; }
.iframe-container { border: 1px solid #d9d9d9; border-radius: 4px; overflow: hidden; }
</style>