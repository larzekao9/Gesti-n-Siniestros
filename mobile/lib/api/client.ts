// Cliente axios del canal asegurado: adjunta el access token (scope='insured') y
// rota el refresh token en 401 (mismo patrón que /frontend/lib/api/client.ts pero
// con expo-secure-store en lugar de localStorage).
import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'

import { API_BASE_URL } from '../config'
import { useAuthStore } from '../stores/authStore'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 20000,
})

api.interceptors.request.use((config) => {
  const { accessToken, tenantSlug } = useAuthStore.getState()
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  if (tenantSlug) {
    config.headers['X-Tenant-Slug'] = tenantSlug
  }
  return config
})

let refreshing: Promise<string | null> | null = null

async function performRefresh(): Promise<string | null> {
  const store = useAuthStore.getState()
  const refreshToken = await store.getRefreshToken()
  if (!refreshToken) return null
  try {
    const resp = await axios.post(`${API_BASE_URL}/insured-auth/refresh`, {
      refresh_token: refreshToken,
    })
    const newAccess: string = resp.data.access_token
    store.setAccessToken(newAccess)
    return newAccess
  } catch {
    await store.logout()
    return null
  }
}

api.interceptors.response.use(
  (resp) => resp,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean
    }
    // Solo los endpoints sin sesión previa NO deben intentar refresh.
    const url = original?.url ?? ''
    const isUnauthEndpoint =
      url.includes('/insured-auth/login') ||
      url.includes('/insured-auth/register') ||
      url.includes('/insured-auth/refresh') ||
      url.includes('/insured-auth/forgot-password') ||
      url.includes('/insured-auth/reset-password') ||
      url.includes('/insured-auth/logout')

    if (
      error.response?.status === 401 &&
      original &&
      !original._retry &&
      !isUnauthEndpoint
    ) {
      original._retry = true
      // Coalesce: un solo refresh aunque varias requests fallen a la vez.
      refreshing = refreshing ?? performRefresh()
      const newToken = await refreshing
      refreshing = null
      if (newToken) {
        original.headers.Authorization = `Bearer ${newToken}`
        return api(original)
      }
    }
    return Promise.reject(error)
  }
)

/** Extrae un mensaje legible de un AxiosError del backend (detail de FastAPI). */
export function apiErrorMessage(err: unknown, fallback = 'Algo salió mal'): string {
  if (axios.isAxiosError(err)) {
    const detail = (err.response?.data as { detail?: unknown } | undefined)?.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail) && detail[0]?.msg) return String(detail[0].msg)
    if (err.message) return err.message
  }
  return fallback
}
