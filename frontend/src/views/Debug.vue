<template>
  <div class="debug">
    <a-page-header
      title="Device Debug"
      sub-title="Debug devices with uiautodev"
    />

    <a-row :gutter="[16, 16]" style="margin-top: 24px">
      <a-col :span="24">
        <a-card title="uiautodev Status">
          <a-descriptions :column="2">
            <a-descriptions-item label="Status">
              <a-tag :color="uiautodevStatus.running ? 'green' : 'red'">
                {{ uiautodevStatus.running ? 'Running' : 'Stopped' }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="URL">
              <a :href="uiautodevStatus.url" target="_blank">{{ uiautodevStatus.url }}</a>
            </a-descriptions-item>
            <a-descriptions-item label="Host">{{ uiautodevStatus.host }}</a-descriptions-item>
            <a-descriptions-item label="Port">{{ uiautodevStatus.port }}</a-descriptions-item>
          </a-descriptions>
          <a-space>
            <a-button type="primary" @click="startUiautodev">Start</a-button>
            <a-button danger @click="stopUiautodev">Stop</a-button>
          </a-space>
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="[16, 16]" style="margin-top: 24px">
      <a-col :span="24">
        <a-card title="Device Inspector">
          <a-select
            v-model:value="selectedDevice"
            placeholder="Select a device"
            style="width: 300px; margin-bottom: 16px"
            @change="handleDeviceChange"
          >
            <a-select-option v-for="device in devices" :key="device.id" :value="device.serial">
              {{ device.name || device.serial }}
            </a-select-option>
          </a-select>
          <div v-if="selectedDevice" class="iframe-container">
            <iframe
              :src="iframeUrl"
              width="100%"
              height="800"
              frameborder="0"
            />
          </div>
          <a-empty v-else description="Select a device to start debugging" />
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
const uiautodevStatus = ref({
  running: false,
  url: '',
  host: '',
  port: 0,
})
const loading = ref(false)

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
  try {
    const res = await axios.get(`/api/debug/uiautodev/device/${serial}`)
    iframeUrl.value = res.data.url
  } catch (error) {
    console.error('Failed to get device URL:', error)
  }
}

onMounted(() => {
  fetchDevices()
  fetchUiautodevStatus()
})
</script>

<style scoped>
.debug {
  padding: 24px;
}

.iframe-container {
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  overflow: hidden;
}
</style>
