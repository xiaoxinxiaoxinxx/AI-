import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  withCredentials: true
})

// 响应拦截器
api.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// ========== 认证 ==========
export const login = (data) => api.post('/login', data)
export const register = (data) => api.post('/register', data)
export const logout = () => api.post('/logout')
export const getCurrentUser = () => api.get('/current_user')

// ========== 患者管理 ==========
export const getPatients = (params) => api.get('/patients', { params })
export const getPatient = (id) => api.get(`/patients/${id}`)
export const addPatient = (data) => api.post('/patients', data)
export const updatePatient = (id, data) => api.put(`/patients/${id}`, data)
export const deletePatient = (id) => api.delete(`/patients/${id}`)
export const getPatientStats = () => api.get('/patients/stats')

// ========== 预测 ==========
export const predictStroke = (data) => api.post('/predict', data)
export const getPredictions = (params) => api.get('/predictions', { params })

// ========== 联邦训练 ==========
export const trainModel = () => api.post('/train')
export const getModelEvaluation = () => api.get('/model/evaluation')
export const getModelParams = () => api.get('/model/params')

// ========== 仪表盘 ==========
export const getDashboard = () => api.get('/dashboard')