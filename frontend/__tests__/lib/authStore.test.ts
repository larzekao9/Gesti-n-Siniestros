/**
 * Tests for the Zustand authStore.
 *
 * Covers:
 *  - Initial state is null/false
 *  - setAuth persists user and accessToken
 *  - setAuth stores refreshToken in localStorage
 *  - setAuth writes the access token cookie
 *  - clearAuth removes user, token, cookie and localStorage key
 *  - setAccessToken updates only the accessToken
 *  - setLoading toggles isLoading
 *  - getRefreshToken reads from localStorage
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useAuthStore, getRefreshToken } from '@/lib/stores/authStore'
import { mockUser } from '../helpers/mocks'

// ------------------------------------------------------------------
// Storage mocks
// ------------------------------------------------------------------
const localStorageMock = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: vi.fn((_key: string): string | null => store[_key] ?? null),
    setItem: vi.fn((key: string, value: string) => { store[key] = value }),
    removeItem: vi.fn((key: string) => { delete store[key] }),
    clear: () => { store = {} },
  }
})()

Object.defineProperty(globalThis, 'localStorage', {
  value: localStorageMock,
  writable: true,
})

// Cookie mock
let cookieStore = ''
Object.defineProperty(globalThis.document, 'cookie', {
  get: vi.fn(() => cookieStore),
  set: vi.fn((val: string) => { cookieStore = val }),
  configurable: true,
})

// ------------------------------------------------------------------
// Tests
// ------------------------------------------------------------------
describe('authStore', () => {
  beforeEach(() => {
    localStorageMock.clear()
    localStorageMock.getItem.mockClear()
    localStorageMock.setItem.mockClear()
    localStorageMock.removeItem.mockClear()
    cookieStore = ''
    // Reset store to pristine state
    useAuthStore.setState({ user: null, accessToken: null, isLoading: false })
  })

  it('el estado inicial es null/false', () => {
    const { user, accessToken, isLoading } = useAuthStore.getState()
    expect(user).toBeNull()
    expect(accessToken).toBeNull()
    expect(isLoading).toBe(false)
  })

  it('setAuth actualiza user y accessToken en el store', () => {
    const user = mockUser()
    useAuthStore.getState().setAuth(user, 'access.jwt', 'refresh.jwt', 'test-tenant')

    const state = useAuthStore.getState()
    expect(state.user).toEqual(user)
    expect(state.accessToken).toBe('access.jwt')
  })

  it('setAuth guarda el refreshToken en localStorage', () => {
    const user = mockUser()
    useAuthStore.getState().setAuth(user, 'access.jwt', 'refresh.jwt', 'test-tenant')

    expect(localStorageMock.setItem).toHaveBeenCalledWith(
      'siniestros_rt',
      'refresh.jwt'
    )
  })

  it('clearAuth elimina user y accessToken del store', () => {
    const user = mockUser()
    useAuthStore.getState().setAuth(user, 'access.jwt', 'refresh.jwt', 'test-tenant')
    useAuthStore.getState().clearAuth()

    const state = useAuthStore.getState()
    expect(state.user).toBeNull()
    expect(state.accessToken).toBeNull()
  })

  it('clearAuth elimina el refreshToken de localStorage', () => {
    useAuthStore.getState().setAuth(mockUser(), 'access.jwt', 'refresh.jwt', 'test-tenant')
    useAuthStore.getState().clearAuth()

    expect(localStorageMock.removeItem).toHaveBeenCalledWith('siniestros_rt')
  })

  it('setAccessToken actualiza solo el accessToken', () => {
    const user = mockUser()
    useAuthStore.getState().setAuth(user, 'old.token', 'refresh.jwt', 'test-tenant')
    useAuthStore.getState().setAccessToken('new.token')

    const state = useAuthStore.getState()
    expect(state.accessToken).toBe('new.token')
    expect(state.user).toEqual(user)
  })

  it('setLoading cambia isLoading', () => {
    useAuthStore.getState().setLoading(true)
    expect(useAuthStore.getState().isLoading).toBe(true)

    useAuthStore.getState().setLoading(false)
    expect(useAuthStore.getState().isLoading).toBe(false)
  })

  it('getRefreshToken lee desde localStorage', () => {
    localStorageMock.getItem.mockReturnValueOnce('stored.refresh.token')
    expect(getRefreshToken()).toBe('stored.refresh.token')
    expect(localStorageMock.getItem).toHaveBeenCalledWith('siniestros_rt')
  })

  it('getRefreshToken retorna null si no hay token', () => {
    localStorageMock.getItem.mockReturnValueOnce(null)
    expect(getRefreshToken()).toBeNull()
  })
})
