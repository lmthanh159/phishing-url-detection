import axios from 'axios'
import { toast } from 'vue3-toastify'

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (!error.response) {
      toast.error('Cannot connect to server')
    } else if (error.response.status === 503) {
      toast.error('Model not available. Please try again later.')
    } else if (error.response.status === 429) {
      toast.warning('Too many requests. Please slow down.')
    } else if (error.response.status >= 500) {
      toast.error('Server error. Please try again.')
    }
    return Promise.reject(error)
  }
)

export default apiClient

export const scanUrl = (url) => apiClient.post('/scan', { url })

export const scanBatch = (formData) =>
  apiClient.post('/scan/batch', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000,
  })

export const explainUrl = (url) => apiClient.post('/explain', { url })

export const getModelInfo = () => apiClient.get('/model-info')

export const getHealth = () => apiClient.get('/health')
