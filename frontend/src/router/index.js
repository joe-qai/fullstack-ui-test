import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Projects from '../views/Projects.vue'
import ProjectDetail from '../views/ProjectDetail.vue'
import POManagement from '../views/POManagement.vue'
import APKManagement from '../views/APKManagement.vue'
import TestCaseManagement from '../views/TestCaseManagement.vue'
import ScriptManagement from '../views/ScriptManagement.vue'
import Devices from '../views/Devices.vue'
import Tasks from '../views/Tasks.vue'
import Reports from '../views/Reports.vue'
import Keywords from '../views/Keywords.vue'
import Debug from '../views/Debug.vue'

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', component: Dashboard, name: 'Dashboard' },
  { path: '/projects', component: Projects, name: 'Projects' },
  { path: '/projects/:id', component: ProjectDetail, name: 'ProjectDetail' },
  { path: '/po', component: POManagement, name: 'PO' },
  { path: '/apk', component: APKManagement, name: 'APK' },
  { path: '/cases', component: TestCaseManagement, name: 'Cases' },
  { path: '/scripts', component: ScriptManagement, name: 'Scripts' },
  { path: '/devices', component: Devices, name: 'Devices' },
  { path: '/tasks', component: Tasks, name: 'Tasks' },
  { path: '/reports', component: Reports, name: 'Reports' },
  { path: '/keywords', component: Keywords, name: 'Keywords' },
  { path: '/debug', component: Debug, name: 'Debug' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
