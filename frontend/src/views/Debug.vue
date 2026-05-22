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
                <a-tag color="green">运行中</a-tag>
                <span>云端服务: uiauto2.devsleep.com</span>
              </a-space>
            </a-col>
            <a-col :span="12" style="text-align: right">
              <a-space>
                <a-button @click="openInNewTab">新窗口打开</a-button>
              </a-space>
            </a-col>
          </a-row>
        </a-card>
      </a-col>

      <a-col :span="24">
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

      <a-col :span="24">
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
  </a-row>
</div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ReloadOutlined, FullscreenOutlined } from '@ant-design/icons-vue'
import { getDevices } from '../api'

const devices = ref([])
const selectedDevice = ref(null)
const loading = ref(false)
const debugIframe = ref(null)
const currentUrl = ref('')
const iframeKey = ref(0)
const iframeHeight = ref(600)

const currentIframeSrc = computed(() => {
  if (currentUrl.value) {
    // 将 /uiautodev/ 前缀替换为完整的云端 URL
    return currentUrl.value.replace('/uiautodev/', 'https://uiauto2.devsleep.com/')
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
  if (selectedDevice.value) {
    window.open(`https://uiauto2.devsleep.com/android/${selectedDevice.value}`, '_blank')
  } else {
    window.open('https://uiauto2.devsleep.com', '_blank')
  }
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
  
  const updateHeight = () => {
    iframeHeight.value = window.innerHeight - 400
  }
  updateHeight()
  window.addEventListener('resize', updateHeight)
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
