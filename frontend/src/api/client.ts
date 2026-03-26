import axios from 'axios'
import type { AxiosError, InternalAxiosRequestConfig } from 'axios'
import { toast } from 'sonner'

const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor: attach Bearer token from localStorage
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('access_token')
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor: error normalization + toasts
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string }>) => {
    if (!error.response) {
      toast.error('Connection error', {
        description: 'Could not connect to the server',
      })
      return Promise.reject(error)
    }

    const status = error.response.status
    const message = error.response.data?.detail || error.message

    if (status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    } else if (status === 403) {
      toast.error('Access denied')
    } else if (status >= 500) {
      toast.error('Server error', {
        description: 'Please try again later',
      })
    }

    return Promise.reject({
      status,
      message,
      body: error.response.data,
    })
  }
)

export default apiClient
