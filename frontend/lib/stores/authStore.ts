import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import type { User } from '@/types/auth'

interface AuthState {
  user: User | null
  accessToken: string | null
  tenantSlug: string | null
  isLoading: boolean
  setAuth: (user: User, accessToken: string, refreshToken: string, tenantSlug: string) => void
  setAccessToken: (accessToken: string) => void
  clearAuth: () => void
  setLoading: (loading: boolean) => void
}

const REFRESH_TOKEN_KEY = 'siniestros_rt'
const ACCESS_TOKEN_COOKIE = 'siniestros_access_token'

function setCookie(name: string, value: string, maxAgeSecs = 3600): void {
  if (typeof document === 'undefined') return
  document.cookie = `${name}=${encodeURIComponent(value)}; path=/; max-age=${maxAgeSecs}; SameSite=Strict`
}

function removeCookie(name: string): void {
  if (typeof document === 'undefined') return
  document.cookie = `${name}=; path=/; max-age=0; SameSite=Strict`
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      tenantSlug: null,
      isLoading: false,

      setAuth: (user, accessToken, refreshToken, tenantSlug) => {
        if (typeof window !== 'undefined') {
          localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
          setCookie(ACCESS_TOKEN_COOKIE, accessToken)
        }
        set({ user, accessToken, tenantSlug })
      },

      setAccessToken: (accessToken) => {
        if (typeof window !== 'undefined') {
          setCookie(ACCESS_TOKEN_COOKIE, accessToken)
        }
        set({ accessToken })
      },

      clearAuth: () => {
        if (typeof window !== 'undefined') {
          localStorage.removeItem(REFRESH_TOKEN_KEY)
          removeCookie(ACCESS_TOKEN_COOKIE)
        }
        set({ user: null, accessToken: null, tenantSlug: null })
      },

      setLoading: (loading) => {
        set({ isLoading: loading })
      },
    }),
    {
      name: 'siniestros_auth',
      storage: createJSONStorage(() =>
        typeof window !== 'undefined' ? localStorage : {
          getItem: () => null,
          setItem: () => undefined,
          removeItem: () => undefined,
        }
      ),
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        tenantSlug: state.tenantSlug,
      }),
    }
  )
)

export function getRefreshToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}
