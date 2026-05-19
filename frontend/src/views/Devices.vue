<template>
  <div class="devices">
    <a-page-header title="设备管理" sub-title="管理测试设备">
      <template #extra>
        <a-button @click="handleScan" :loading="scanning">扫描设备</a-button>
      </template>
    </a-page-header>

    <a-table :columns="columns" :data-source="devices" :loading="loading" row-key="id" style="margin-top: 16px">
      <template #status="{ record }">
        <a-tag :color="record.status === 'online' ? 'green' : 'red'">{{ record.status }}</a-tag>
      </template>
      <template #connType="{ record }">
        <a-tag :color="isTcpipDevice(record.serial) ? 'blue' : 'default'">
          {{ isTcpipDevice(record.serial) ? 'TCP/IP' : 'USB' }}
        </a-tag>
      </template>
      <template #action="{ record }">
        <a-button v-if="isTcpipDevice(record.serial)" type="link" danger @click="handleDisconnect(record)">断开</a-button>
        <a-button v-else type="link" @click="handleConnect(record)">连接</a-button>
      </template>
    </a-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { getDevices, scanDevices, disconnectDevice, connectDeviceOneClick } from '../api'

const devices = ref([])
const loading = ref(false)
const scanning = ref(false)

const isTcpipDevice = (serial) => {
  return serial && serial.includes(':')
}

const columns = [
  { title: '名称', dataIndex: 'name', key: 'name' },
  { title: '序列号', dataIndex: 'serial', key: 'serial' },
  { title: '平台', dataIndex: 'platform', key: 'platform' },
  { title: '连接方式', key: 'connType', slots: { customRender: 'connType' } },
  { title: '状态', dataIndex: 'status', key: 'status', slots: { customRender: 'status' } },
  { title: '操作', key: 'action', slots: { customRender: 'action' } },
]

const fetchDevices = async () => {
  loading.value = true
  try {
    const res = await getDevices()
    devices.value = res.data
  } catch (error) {
    message.error('获取设备列表失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

const handleScan = async () => {
  scanning.value = true
  try {
    await scanDevices()
    await fetchDevices()
  } catch (error) {
    message.error('扫描设备失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    scanning.value = false
  }
}

const handleConnect = async (device) => {
  try {
    const res = await connectDeviceOneClick(device.serial)
    message.success(res.data.message)
    setTimeout(() => fetchDevices(), 2000)
  } catch (error) {
    message.error('连接失败: ' + (error.response?.data?.detail || error.message))
  }
}

const handleDisconnect = async (device) => {
  try {
    const parts = device.serial.split(':')
    await disconnectDevice(parts[0], parseInt(parts[1]) || 5555)
    message.success('已断开连接')
    setTimeout(() => fetchDevices(), 1000)
  } catch (error) {
    message.error('断开连接失败: ' + (error.response?.data?.detail || error.message))
  }
}

onMounted(fetchDevices)
</script>

<style scoped>
.devices { padding: 24px; }
</style>