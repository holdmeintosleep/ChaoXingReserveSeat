import axios from 'axios'

let baseURL = '/api'

if (window.electronAPI) {
  baseURL = 'http://localhost:5000/api'
}

const client = axios.create({
  baseURL,
  timeout: 10000
})

export const configApi = {
  // 配置管理
  getAll: () => client.get('/config'),
  getReserveList: () => client.get('/config/reserve'),
  getReserve: (index) => client.get(`/config/reserve/${index}`),
  addReserve: (data) => client.post('/config/reserve', data),
  updateReserve: (index, data) => client.put(`/config/reserve/${index}`, data),
  deleteReserve: (index) => client.delete(`/config/reserve/${index}`),
  exportConfig: () => client.get('/config/export', { responseType: 'blob' }),
  validateConfig: (data) => client.post('/config/validate', data),
  getSignin: () => client.get('/config/signin'),
  updateSignin: (data) => client.put('/config/signin', data),
  getRules: () => client.get('/rules'),

  // 预约执行
  executeReservation: (configIndex) => client.post('/reservation/execute', { config_index: configIndex }),
  getReservationStatus: (taskId) => client.get(`/reservation/status/${taskId}`),
  getReservationHistory: (username) => client.get('/reservation/history', { params: username ? { username } : {} }),
  clearReservationHistory: (username) => client.delete('/reservation/history', { params: username ? { username } : {} }),

  // 签到执行
  executeSignin: (data) => client.post('/signin/execute', data),
  cancelSignin: (data) => client.post('/signin/cancel', data),
  getSigninStatus: (params) => client.get('/signin/status', { params }),
  batchSignin: (configIndex) => client.post('/signin/batch', { config_index: configIndex }),

  // 定时任务调度
  getTasks: (status) => client.get('/scheduler/tasks', { params: status ? { status } : {} }),
  getTask: (taskId) => client.get(`/scheduler/tasks/${taskId}`),
  createTask: (data) => client.post('/scheduler/tasks', data),
  cancelTask: (taskId) => client.delete(`/scheduler/tasks/${taskId}`),
  startScheduler: () => client.post('/scheduler/start'),
  stopScheduler: () => client.post('/scheduler/stop'),
  getSchedulerStatus: () => client.get('/scheduler/status'),
  autoSchedule: (configIndex) => client.post('/scheduler/auto_schedule', configIndex ? { config_index: configIndex } : {}),

  // 日志管理
  getLogs: (params) => client.get('/logs', { params }),
  exportLogs: (data) => client.post('/logs/export', data),
  getLogStats: (days) => client.get('/logs/stats', { params: days ? { days } : {} }),
  clearLogs: (daysToKeep) => client.post('/logs/clear', { days_to_keep: daysToKeep })
}

export default configApi