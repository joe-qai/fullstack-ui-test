import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Projects from '../views/Projects.vue'
import ProjectDetail from '../views/ProjectDetail.vue'
import Devices from '../views/Devices.vue'
import Tasks from '../views/Tasks.vue'
import Keywords from '../views/Keywords.vue'

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', component: Dashboard, name: 'Dashboard' },
  { path: '/projects', component: Projects, name: 'Projects' },
  { path: '/projects/:id', component: ProjectDetail, name: 'ProjectDetail' },
  { path: '/devices', component: Devices, name: 'Devices' },
  { path: '/tasks', component: Tasks, name: 'Tasks' },
  { path: '/keywords', component: Keywords, name: 'Keywords' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
