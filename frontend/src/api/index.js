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
export const batchDeleteCases = (projectId, ids) => api.post(`/api/projects/${projectId}/cases/batch-delete`, { ids })

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
export const deleteTask = (taskId) => api.delete(`/api/tasks/${taskId}`)
export const batchDeleteTasks = (ids) => api.post('/api/tasks/batch-delete', { ids })

// APK Management
export const getApks = () => api.get('/api/apks')
export const uploadApk = (file, version, description) => {
  const formData = new FormData()
  formData.append('file', file)
  if (version) formData.append('version', version)
  if (description) formData.append('description', description)
  return api.post('/api/apks', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
export const deleteApk = (apkId) => api.delete(`/api/apks/${apkId}`)

// Case update/delete
export const updateCase = (projectId, caseId, data) => api.put(`/api/projects/${projectId}/cases/${caseId}`, data)
export const deleteCase = (projectId, caseId) => api.delete(`/api/projects/${projectId}/cases/${caseId}`)

// Device TCP/IP
export const tcpipDevice = (serial, port = 5555) => api.post('/api/devices/tcpip', { serial, port })
export const connectDevice = (ip, port = 5555) => api.post('/api/devices/connect', { ip, port })
export const disconnectDevice = (ip, port = 5555) => api.post('/api/devices/disconnect', { ip, port })
export const connectDeviceOneClick = (serial) => api.post(`/api/devices/${serial}/connect`)

// Element update/delete
export const updateElement = (projectId, pageId, elementId, data) => api.put(`/api/projects/${projectId}/pages/${pageId}/elements/${elementId}`, data)
export const deleteElement = (projectId, pageId, elementId) => api.delete(`/api/projects/${projectId}/pages/${pageId}/elements/${elementId}`)

// Script update, delete, download
export const updateScript = (projectId, scriptId, data) => api.put(`/api/projects/${projectId}/scripts/${scriptId}`, data)
export const deleteScript = (projectId, scriptId) => api.delete(`/api/projects/${projectId}/scripts/${scriptId}`)
export const batchDeleteScripts = (ids) => api.post('/api/projects/scripts/batch-delete', { ids })
export const getScriptDownloadUrl = (projectId, scriptId) => `/api/projects/${projectId}/scripts/${scriptId}/download`
export const getScriptContent = (projectId, scriptId) => api.get(`/api/projects/${projectId}/scripts/${scriptId}/content`)
export const updateScriptContent = (projectId, scriptId, content) => api.put(`/api/projects/${projectId}/scripts/${scriptId}/content`, { content })

// Keywords CRUD
export const createCustomKeyword = (projectId, data) => api.post(`/api/projects/${projectId}/custom-keywords`, data)
export const updateKeyword = (id, data) => api.put(`/api/keywords/${id}`, data)
export const deleteKeyword = (id) => api.delete(`/api/keywords/${id}`)

// Stats
export const getStats = () => api.get('/api/stats')

// Project stats
export const getProjectStats = (id) => api.get(`/api/projects/${id}/stats`)

// Reports
export const getReports = () => api.get('/api/reports')
export const getTaskReport = (taskId) => api.get(`/api/tasks/${taskId}/report`)
export const deleteReport = (reportId) => api.delete(`/api/reports/${reportId}`)
export const batchDeleteReports = (ids) => api.post('/api/reports/batch-delete', { ids })
export const getReportDownloadUrl = (reportId, format = 'html') => `/api/reports/${reportId}/download?format=${format}`
export const getReportViewUrl = (reportId) => `/api/reports/${reportId}/view`

// Page copy
export const copyPage = (projectId, sourcePageId) =>
  api.post(`/api/projects/${projectId}/pages/copy-from`, { source_page_id: sourcePageId })

// Global scripts
export const getAllScripts = () => api.get('/api/projects/scripts')

// Global cases
export const getAllCases = () => api.get('/api/projects/cases')

export default api
