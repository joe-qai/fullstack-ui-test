import axios from 'axios'

const api = axios.create({
  baseURL: '',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Projects
export const getProjects = () => api.get('/api/projects')
export const createProject = (data) => api.post('/api/projects', data)
export const getProject = (id) => api.get(`/api/projects/${id}`)
export const updateProject = (id, data) => api.put(`/api/projects/${id}`, data)
export const deleteProject = (id) => api.delete(`/api/projects/${id}`)

// Pages & Elements
export const getPages = (projectId) => api.get(`/api/projects/${projectId}/pages`)
export const createPage = (projectId, data) => api.post(`/api/projects/${projectId}/pages`, data)
export const getPage = (projectId, pageId) => api.get(`/api/projects/${projectId}/pages/${pageId}`)
export const updatePage = (projectId, pageId, data) => api.put(`/api/projects/${projectId}/pages/${pageId}`, data)
export const deletePage = (projectId, pageId) => api.delete(`/api/projects/${projectId}/pages/${pageId}`)
export const getElements = (projectId, pageId) => api.get(`/api/projects/${projectId}/pages/${pageId}/elements`)
export const createElement = (projectId, pageId, data) => api.post(`/api/projects/${projectId}/pages/${pageId}/elements`, data)

// Keywords
export const getKeywords = (params) => api.get('/api/keywords', { params })
export const getKeywordCategories = () => api.get('/api/keywords/categories')

// Test Cases
export const getCases = (projectId) => api.get(`/api/projects/${projectId}/cases`)
export const createCase = (projectId, data) => api.post(`/api/projects/${projectId}/cases`, data)

// Scripts
export const getScripts = (projectId) => api.get(`/api/projects/${projectId}/scripts`)
export const uploadScript = (projectId, file) => {
  const formData = new FormData()
  formData.append('file', file)
  return api.post(`/api/projects/${projectId}/scripts`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

// Devices
export const getDevices = () => api.get('/api/devices')
export const scanDevices = () => api.post('/api/devices/scan')

// Tasks
export const getTasks = () => api.get('/api/tasks')
export const createTask = (data) => api.post('/api/tasks', data)
export const executeTask = (taskId) => api.post(`/api/tasks/${taskId}/execute`)

// APK Management
export const getApks = (projectId) => api.get(`/api/projects/${projectId}/apks`)
export const uploadApk = (projectId, file, version, description) => {
  const formData = new FormData()
  formData.append('file', file)
  if (version) formData.append('version', version)
  if (description) formData.append('description', description)
  return api.post(`/api/projects/${projectId}/apks`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
export const deleteApk = (projectId, apkId) => api.delete(`/api/projects/${projectId}/apks/${apkId}`)

// Case update/delete
export const updateCase = (projectId, caseId, data) => api.put(`/api/projects/${projectId}/cases/${caseId}`, data)
export const deleteCase = (projectId, caseId) => api.delete(`/api/projects/${projectId}/cases/${caseId}`)

// Device TCP/IP
export const tcpipDevice = (serial, port = 5555) => api.post('/api/devices/tcpip', { serial, port })
export const connectDevice = (ip, port = 5555) => api.post('/api/devices/connect', { ip, port })
export const disconnectDevice = (ip, port = 5555) => api.post('/api/devices/disconnect', { ip, port })

// Element update/delete
export const updateElement = (projectId, pageId, elementId, data) => api.put(`/api/projects/${projectId}/pages/${pageId}/elements/${elementId}`, data)
export const deleteElement = (projectId, pageId, elementId) => api.delete(`/api/projects/${projectId}/pages/${pageId}/elements/${elementId}`)

// Script delete
export const deleteScript = (projectId, scriptId) => api.delete(`/api/projects/${projectId}/scripts/${scriptId}`)

// Stats
export const getStats = () => api.get('/api/stats')

export default api
