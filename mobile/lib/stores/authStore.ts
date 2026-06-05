// Sesión del asegurado con Zustand. El access token vive en memoria; el refresh
// token va a expo-secure-store (Keychain iOS / KeyStore Android) — nunca en
// AsyncStorage/localStorage (ADR-005 adaptado al móvil, §6.7.2).
import * as SecureStore from 'expo-secure-store'
import { create } from 'zustand'

import { SECURE_KEYS } from '../config'
import type { Account } from '@/types/auth'

interface AuthState {
  account: Account | null
  accessToken: string | null
  tenantSlug: string | null
  hydrated: boolean
  setSession: (args: {
    account: Account
    accessToken: string
    refreshToken: string
    tenantSlug: string
  }) => Promise<void>
  setAccessToken: (token: string) => void
  getRefreshToken: () => Promise<string | null>
  hydrate: () => Promise<void>
  logout: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set, get) => ({
  account: null,
  accessToken: null,
  tenantSlug: null,
  hydrated: false,

  setSession: async ({ account, accessToken, refreshToken, tenantSlug }) => {
    await SecureStore.setItemAsync(SECURE_KEYS.refreshToken, refreshToken)
    set({ account, accessToken, tenantSlug })
  },

  setAccessToken: (token) => set({ accessToken: token }),

  getRefreshToken: async () => {
    return SecureStore.getItemAsync(SECURE_KEYS.refreshToken)
  },

  // Al abrir la app: si hay refresh token guardado, marcamos hydrated para que
  // el guard de rutas intente refrescar. El access token se obtiene on-demand.
  hydrate: async () => {
    const refresh = await SecureStore.getItemAsync(SECURE_KEYS.refreshToken)
    set({ hydrated: true })
    if (!refresh) {
      set({ accessToken: null, account: null })
    }
  },

  logout: async () => {
    await SecureStore.deleteItemAsync(SECURE_KEYS.refreshToken)
    set({ account: null, accessToken: null, tenantSlug: null })
  },
}))
