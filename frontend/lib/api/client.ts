import axios, {
  AxiosError,
  type AxiosInstance,
  type InternalAxiosRequestConfig,
} from 'axios'
import { useAuthStore, getRefreshToken } from '@/lib/stores/authStore'

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api'

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
})

// Track whether we are already refreshing to avoid concurrent refresh loops
let isRefreshing = false
let failedQueue: Array<{
  resolve: (value: string) => void
  reject: (reason: unknown) => void
}> = []

function processQueue(error: unknown, token: string | null = null): void {
  failedQueue.forEach((promise) => {
    if (error) {
      promise.reject(error)
    } else if (token) {
      promise.resolve(token)
    }
  })
  failedQueue = []
}

// Request interceptor: inject JWT + tenant
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const { accessToken, tenantSlug } = useAuthStore.getState()
    if (accessToken && config.headers) {
      config.headers.Authorization = `Bearer ${accessToken}`
    }
    if (tenantSlug && config.headers) {
      config.headers['X-Tenant-Slug'] = tenantSlug
    }
    return config
  },
  (error: unknown) => Promise.reject(error)
)

// Response interceptor: silent token refresh on 401
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean
    }

    if (error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error)
    }

    const refreshToken = getRefreshToken()
    if (!refreshToken) {
      useAuthStore.getState().clearAuth()
      if (typeof window !== 'undefined') {
        window.location.href = '/login'
      }
      return Promise.reject(error)
    }

    if (isRefreshing) {
      return new Promise<string>((resolve, reject) => {
        failedQueue.push({ resolve, reject })
      })
        .then((token) => {
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${token}`
          }
          return apiClient(originalRequest)
        })
        .catch((err: unknown) => Promise.reject(err))
    }

    originalRequest._retry = true
    isRefreshing = true

    try {
      const { data } = await axios.post<{ access_token: string }>(
        `${API_BASE_URL}/auth/refresh`,
        { refresh_token: refreshToken }
      )
      const newAccessToken = data.access_token
      useAuthStore.getState().setAccessToken(newAccessToken)
      processQueue(null, newAccessToken)

      if (originalRequest.headers) {
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
      }
      return apiClient(originalRequest)
    } catch (refreshError: unknown) {
      processQueue(refreshError, null)
      useAuthStore.getState().clearAuth()
      if (typeof window !== 'undefined') {
        window.location.href = '/login'
      }
      return Promise.reject(refreshError)
    } finally {
      isRefreshing = false
    }
  }
)

export default apiClient
