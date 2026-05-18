<template>
  <a-layout style="min-height: 100vh">
    <a-layout-sider v-model:collapsed="collapsed" collapsible>
      <div class="logo">
        <span v-if="!collapsed">AutoTest</span>
      </div>
      <a-menu
        v-model:selectedKeys="selectedKeys"
        theme="dark"
        mode="inline"
        @click="handleMenuClick"
      >
        <a-menu-item key="dashboard">
          <DashboardOutlined />
          <span>Dashboard</span>
        </a-menu-item>
        <a-menu-item key="projects">
          <ProjectOutlined />
          <span>Projects</span>
        </a-menu-item>
        <a-menu-item key="devices">
          <MobileOutlined />
          <span>Devices</span>
        </a-menu-item>
        <a-menu-item key="tasks">
          <PlayCircleOutlined />
          <span>Tasks</span>
        </a-menu-item>
        <a-menu-item key="keywords">
          <KeyOutlined />
          <span>Keywords</span>
        </a-menu-item>
        <a-menu-item key="debug">
          <BugOutlined />
          <span>Debug</span>
        </a-menu-item>
      </a-menu>
    </a-layout-sider>
    <a-layout>
      <a-layout-header style="background: #fff; padding: 0 24px">
        <h2 style="margin: 0; line-height: 64px">UI AutoTest Platform</h2>
      </a-layout-header>
      <a-layout-content style="margin: 24px">
        <router-view />
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  DashboardOutlined,
  ProjectOutlined,
  MobileOutlined,
  PlayCircleOutlined,
  KeyOutlined,
  BugOutlined,
} from '@ant-design/icons-vue'

const router = useRouter()
const route = useRoute()
const collapsed = ref(false)
const selectedKeys = ref([route.name?.toLowerCase() || 'dashboard'])

const handleMenuClick = ({ key }) => {
  router.push(`/${key}`)
}
</script>

<style scoped>
.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
}
</style>
