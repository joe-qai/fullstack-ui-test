<template>
  <div class="debug">
    <a-row :gutter="[8, 8]">
      <a-col :span="24">
        <a-card size="small" class="toolbar-card">
          <a-row :gutter="8" align="middle">
            <a-col :flex="1">
              <a-space wrap>
                <a-tag :color="serviceStatus.running ? 'green' : 'red'">
                  {{ serviceStatus.running ? '运行中' : '已停止' }}
                </a-tag>
                <span class="service-name">
                  {{ serviceStatus.running ? `本地服务: ${serviceStatus.url}` : 'uiauto.dev 服务未启动' }}
                </span>
              </a-space>
            </a-col>
            <a-col :flex="none">
              <a-space wrap size="small">
                <a-button 
                  size="small" 
                  @click="toggleService"
                  :type="serviceStatus.running ? 'default' : 'primary'"
                  :loading="serviceLoading"
                >
                  {{ serviceStatus.running ? '停止服务' : '启动服务' }}
                </a-button>
                <a-button 
                  size="small" 
                  @click="restartService"
                  :disabled="!serviceStatus.running || serviceLoading"
                >
                  <template #icon><ReloadOutlined /></template>
                  重启服务
                </a-button>
                <a-divider type="vertical" />
                <a-select v-model:value="selectedDevice" placeholder="选择设备" style="width: 260px" @change="handleDeviceChange">
                  <a-select-option v-for="device in devices" :key="device.id" :value="device.serial">
                    {{ device.name || device.serial }}
                    <a-tag v-if="device.serial?.includes(':')" color="blue" size="small">WiFi</a-tag>
                    <a-tag v-else color="green" size="small">USB</a-tag>
                  </a-select-option>
                </a-select>
                <a-button type="primary" size="small" @click="loadDevice" :disabled="!selectedDevice">
                  加载设备
                </a-button>
                <a-button size="small" @click="loadRoot">
                  加载主页
                </a-button>
                <a-button size="small" @click="openInNewTab">新窗口打开</a-button>
                <a-button size="small" @click="refreshIframe">
                  <template #icon><ReloadOutlined /></template>
                  刷新
                </a-button>
                <a-button size="small" @click="fullscreen">
                  <template #icon><FullscreenOutlined /></template>
                  全屏
                </a-button>
              </a-space>
            </a-col>
          </a-row>
        </a-card>
      </a-col>

      <a-col :span="24" class="iframe-col">
        <a-card size="small" class="iframe-card">
          <div class="iframe-container" :style="{ height: iframeHeight + 'px' }">
            <div v-if="loading" class="iframe-loading">
              <a-spin size="large" tip="加载中..." />
            </div>
            <iframe 
              v-show="!loading"
              ref="debugIframe"
              :key="iframeKey"
              :src="currentIframeSrc" 
              @load="onIframeLoad"
              frameborder="0" 
              allowfullscreen
            ></iframe>
          </div>
        </a-card>
      </a-col>
  </a-row>
</div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ReloadOutlined, FullscreenOutlined } from '@ant-design/icons-vue'
import { getDevices } from '../api'
import axios from 'axios'

const devices = ref([])
const selectedDevice = ref(null)
const loading = ref(false)
const debugIframe = ref(null)
const currentUrl = ref('')
const iframeKey = ref(0)
const iframeHeight = ref(600)
const serviceStatus = ref({
  running: false,
  url: '',
  host: '',
  port: 0,
})
const serviceLoading = ref(false)

const currentIframeSrc = computed(() => {
  if (currentUrl.value) {
    if (serviceStatus.value.running) {
      return `http://${serviceStatus.value.host}:${serviceStatus.value.port}${currentUrl.value.replace('/uiautodev', '')}`
    }
    return currentUrl.value.replace('/uiautodev/', 'https://uiauto2.devsleep.com/')
  }
  if (serviceStatus.value.running) {
    return `http://${serviceStatus.value.host}:${serviceStatus.value.port}/`
  }
  return 'https://uiauto2.devsleep.com/'
})

const fetchDevices = async () => {
  try {
    const res = await getDevices()
    devices.value = res.data
  } catch (error) {
    console.error('Failed to fetch devices:', error)
  }
}

const fetchServiceStatus = async () => {
  try {
    const res = await axios.get('/api/debug/uiautodev/status')
    serviceStatus.value = res.data
  } catch (error) {
    serviceStatus.value = { running: false, url: '', host: '', port: 0 }
    console.error('Failed to fetch service status:', error)
  }
}

const startService = async () => {
  try {
    serviceLoading.value = true
    const res = await axios.post('/api/debug/uiautodev/start')
    if (res.data.success) {
      serviceStatus.value = res.data.status
      console.log('Service started successfully')
    }
  } catch (error) {
    console.error('Failed to start service:', error)
  } finally {
    serviceLoading.value = false
  }
}

const stopService = async () => {
  try {
    serviceLoading.value = true
    const res = await axios.post('/api/debug/uiautodev/stop')
    if (res.data.success) {
      serviceStatus.value = res.data.status
      console.log('Service stopped successfully')
    }
  } catch (error) {
    console.error('Failed to stop service:', error)
  } finally {
    serviceLoading.value = false
  }
}

const restartService = async () => {
  try {
    serviceLoading.value = true
    const res = await axios.post('/api/debug/uiautodev/restart')
    if (res.data.success) {
      serviceStatus.value = res.data.status
      console.log('Service restarted successfully')
      refreshIframe()
    }
  } catch (error) {
    console.error('Failed to restart service:', error)
  } finally {
    serviceLoading.value = false
  }
}

const toggleService = () => {
  if (serviceStatus.value.running) {
    stopService()
  } else {
    startService()
  }
}

const reloadIframe = (newUrl) => {
  loading.value = true
  currentUrl.value = newUrl
  iframeKey.value++
}

const handleDeviceChange = (serial) => {
  if (!serial) return
  currentUrl.value = `/uiautodev/android/${serial}`
}

const loadDevice = () => {
  if (!selectedDevice.value) return
  reloadIframe(`/uiautodev/android/${selectedDevice.value}`)
}

const loadRoot = () => {
  reloadIframe('/uiautodev/')
}

const openInNewTab = () => {
  const url = currentIframeSrc.value
  window.open(url, '_blank')
}

const refreshIframe = () => {
  if (currentUrl.value) {
    reloadIframe(currentUrl.value)
  } else {
    reloadIframe('/uiautodev/')
  }
}

const fullscreen = () => {
  if (debugIframe.value) {
    if (debugIframe.value.requestFullscreen) {
      debugIframe.value.requestFullscreen()
    }
  }
}

const onIframeLoad = () => {
  loading.value = false
}

onMounted(() => {
  fetchDevices()
  fetchServiceStatus()
  
  const updateHeight = () => {
    iframeHeight.value = Math.max(window.innerHeight - 160, 500)
  }
  updateHeight()
  window.addEventListener('resize', updateHeight)
})
</script>

<style scoped>
.debug { 
  padding: 0;
  width: 100%;
  height: 100%;
  min-width: 0;
  box-sizing: border-box;
  overflow: auto;
}

.debug :deep(.ant-row) {
  margin: 0;
  min-width: 0;
}

.debug :deep(.ant-col) {
  min-width: 0;
  padding: 0 8px;
}

.debug :deep(.ant-card) {
  margin-bottom: 8px;
  min-width: 0;
}

.debug :deep(.ant-card:first-child) {
  margin-top: 0;
}

.debug :deep(.ant-card:last-child) {
  margin-bottom: 0;
}

.debug :deep(.ant-card-body) {
  padding: 12px;
}

.toolbar-card :deep(.ant-card-body) {
  padding: 8px 12px;
}

.debug :deep(.ant-space) {
  flex-wrap: wrap;
  min-width: 0;
}

.debug :deep(.ant-select) {
  min-width: 200px;
  max-width: 100%;
}

.service-name {
  color: #666;
  font-size: 14px;
}

.iframe-col {
  flex: 1;
}

.iframe-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.iframe-card :deep(.ant-card-body) {
  flex: 1;
  padding: 0;
  display: flex;
  overflow: hidden;
}

.iframe-container {
  position: relative;
  background: #f0f2f5;
  border-radius: 4px;
  overflow: auto;
  width: 100%;
  height: 100%;
  min-width: 0;
  flex: 1;
}

.iframe-container iframe {
  display: block;
  width: 100%;
  min-width: 1024px;
  height: 100%;
  min-height: 768px;
  border: 0;
  overflow: auto;
}

.iframe-loading {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.8);
  z-index: 10;
}
</style>
