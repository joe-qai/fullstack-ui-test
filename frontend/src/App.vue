<template>
  <a-layout style="min-height: 100vh">
    <a-layout-sider v-model:collapsed="collapsed" collapsible>
<div class="logo">
  <span v-if="!collapsed">UiTesting</span>
</div>
      <a-menu
        v-model:selectedKeys="selectedKeys"
        v-model:openKeys="openKeys"
        theme="dark"
        mode="inline"
        @click="handleMenuClick"
      >
        <a-menu-item key="dashboard">
          <DashboardOutlined />
          <span>仪表盘</span>
        </a-menu-item>
        <a-sub-menu key="resources">
          <template #icon>
            <AppstoreOutlined />
          </template>
          <template #title>资源管理</template>
          <a-menu-item key="projects">
            <ProjectOutlined />
            <span>项目管理</span>
          </a-menu-item>
          <a-menu-item key="apk">
            <AndroidOutlined />
            <span>APK管理</span>
          </a-menu-item>
          <a-menu-item key="devices">
            <MobileOutlined />
            <span>设备管理</span>
          </a-menu-item>
        </a-sub-menu>
        <a-menu-item key="keywords">
          <KeyOutlined />
          <span>关键字管理</span>
        </a-menu-item>
        <a-menu-item key="po">
          <AppstoreOutlined />
          <span>对象管理</span>
        </a-menu-item>
        <a-sub-menu key="casescripts">
          <template #icon>
            <FileTextOutlined />
          </template>
          <template #title>用例脚本</template>
          <a-menu-item key="cases">
            <FileTextOutlined />
            <span>用例管理</span>
          </a-menu-item>
          <a-menu-item key="scripts">
            <CodeOutlined />
            <span>脚本管理</span>
          </a-menu-item>
          <a-menu-item key="debug">
            <BugOutlined />
            <span>在线调试</span>
          </a-menu-item>
        </a-sub-menu>
        <a-sub-menu key="execution">
          <template #icon>
            <PlayCircleOutlined />
          </template>
          <template #title>执行中心</template>
          <a-menu-item key="tasks">
            <PlayCircleOutlined />
            <span>任务管理</span>
          </a-menu-item>
          <a-menu-item key="reports">
            <BarChartOutlined />
            <span>报告管理</span>
          </a-menu-item>
        </a-sub-menu>
      </a-menu>
    </a-layout-sider>
    <a-layout>
      <a-layout-header style="background: #fff; padding: 0 24px">
        <h2 style="margin: 0; line-height: 64px">UiTesting Platform</h2>
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
  AppstoreOutlined,
  AndroidOutlined,
  CodeOutlined,
  FileTextOutlined,
  MobileOutlined,
  PlayCircleOutlined,
  BarChartOutlined,
  KeyOutlined,
  BugOutlined,
} from '@ant-design/icons-vue'

const router = useRouter()
const route = useRoute()
const collapsed = ref(false)
const openKeys = ref(['resources', 'casescripts', 'execution'])
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
