<template>
  <div class="debug">
    <a-page-header title="在线调试" sub-title="使用 uiautodev 调试真机设备" />

    <a-row :gutter="[16, 16]" style="margin-top: 24px">
      <a-col :span="24">
        <a-card title="uiautodev 服务状态" size="small">
          <a-row :gutter="16" align="middle">
            <a-col :span="12">
              <a-space>
                <span>状态:</span>
                <a-tag :color="uiautodevStatus.running ? 'green' : 'red'">
                  {{ uiautodevStatus.running ? '运行中' : '已停止' }}
                </a-tag>
                <span v-if="uiautodevStatus.running">端口: {{ uiautodevStatus.port }}</span>
              </a-space>
            </a-col>
            <a-col :span="12" style="text-align: right">
              <a-space>
                <a-button type="primary" :loading="starting" @click="startUiautodev" :disabled="uiautodevStatus.running">
                  启动服务
                </a-button>
                <a-button danger @click="stopUiautodev" :disabled="!uiautodevStatus.running">
                  停止服务
                </a-button>
                <a-button @click="openInNewTab" :disabled="!uiautodevStatus.running">
                  新窗口打开
                </a-button>
              </a-space>
            </a-col>
          </a-row>
        </a-card>
      </a-col>

      <a-col :span="24" v-if="uiautodevStatus.running">
        <a-card title="设备选择" size="small">
          <a-space>
            <a-select v-model:value="selectedDevice" placeholder="选择要调试的设备" style="width: 300px" @change="handleDeviceChange">
              <a-select-option v-for="device in devices" :key="device.id" :value="device.serial">
                {{ device.name || device.serial }}
                <a-tag v-if="device.serial?.includes(':')" color="blue" size="small">WiFi</a-tag>
                <a-tag v-else color="green" size="small">USB</a-tag>
              </a-select-option>
            </a-select>
            <a-button type="primary" @click="loadDevice" :disabled="!selectedDevice">
              加载设备
            </a-button>
            <a-button @click="loadRoot">
              加载主页
            </a-button>
          </a-space>
        </a-card>
      </a-col>

      <a-col :span="24" v-if="uiautodevStatus.running">
        <a-card size="small">
          <template #title>
            <a-space>
              <span>调试界面</span>
              <a-tag v-if="currentUrl" color="blue">{{ currentUrl }}</a-tag>
            </a-space>
          </template>
          <template #extra>
            <a-button-group size="small">
              <a-button @click="refreshIframe">
                <template #icon><ReloadOutlined /></template>
                刷新
              </a-button>
              <a-button @click="fullscreen">
                <template #icon><FullscreenOutlined /></template>
                全屏
              </a-button>
            </a-button-group>
          </template>
          
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
              style="width: 100%; height: 100%; border: none;"
              allowfullscreen
            ></iframe>
          </div>
        </a-card>
      </a-col>

      <a-col :span="24" v-else>
        <a-card>
          <a-empty description="uiautodev 服务未启动，请先启动服务">
            <a-button type="primary" @click="startUiautodev">启动服务</a-button>
          </a-empty>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import axios from 'axios'
import { message } from 'ant-design-vue'
import { ReloadOutlined, FullscreenOutlined } from '@ant-design/icons-vue'
import { getDevices } from '../api'

const devices = ref([])
const selectedDevice = ref(null)
const uiautodevStatus = ref({ running: false, url: '', host: '', port: 0 })
const starting = ref(false)
const loading = ref(false)
const debugIframe = ref(null)
const currentUrl = ref('')
const iframeKey = ref(0)
const iframeHeight = ref(600)

const currentIframeSrc = computed(() => {
  if (!uiautodevStatus.value.running) return ''
  if (currentUrl.value) return currentUrl.value
  return '/uiautodev/'
})

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

const reloadIframe = (newUrl) => {
  loading.value = true
  currentUrl.value = newUrl
  iframeKey.value++
}

const startUiautodev = async () => {
  starting.value = true
  try {
    const res = await axios.post('/api/debug/uiautodev/start')
    if (res.data.success) {
      message.success('uiautodev 服务启动成功')
      await fetchUiautodevStatus()
      setTimeout(() => {
        reloadIframe('/uiautodev/')
      }, 1000)
    } else {
      message.error('uiautodev 服务启动失败')
    }
  } catch (error) {
    message.error('启动失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    starting.value = false
  }
}

const stopUiautodev = async () => {
  try {
    await axios.post('/api/debug/uiautodev/stop')
    message.success('uiautodev 服务已停止')
    await fetchUiautodevStatus()
    currentUrl.value = ''
  } catch (error) {
    message.error('停止失败: ' + (error.response?.data?.detail || error.message))
  }
}

const handleDeviceChange = async (serial) => {
  if (!serial) return
  try {
    const res = await axios.get(`/api/debug/uiautodev/device/${serial}`)
    currentUrl.value = `/uiautodev/android/${serial}`
  } catch (error) {
    message.error('获取设备调试 URL 失败')
  }
}

const loadDevice = () => {
  if (!selectedDevice.value) return
  reloadIframe(`/uiautodev/android/${selectedDevice.value}`)
}

const loadRoot = () => {
  reloadIframe('/uiautodev/')
}

const openInNewTab = () => {
  window.open(uiautodevStatus.value.url, '_blank')
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
  fetchUiautodevStatus()
  
  const updateHeight = () => {
    iframeHeight.value = window.innerHeight - 400
  }
  updateHeight()
  window.addEventListener('resize', updateHeight)
})

watch(() => uiautodevStatus.value.running, (newVal) => {
  if (newVal && !currentUrl.value) {
    reloadIframe('/uiautodev/')
  }
})
</script>

<style scoped>
.debug { 
  padding: 24px; 
}

.iframe-container {
  position: relative;
  background: #f0f2f5;
  border-radius: 4px;
  overflow: hidden;
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
