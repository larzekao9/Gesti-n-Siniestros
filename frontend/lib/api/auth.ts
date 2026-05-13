import apiClient from './client'
import type {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  MFASetupResponse,
  MFAVerifyResponse,
  RefreshResponse,
} from '@/types/auth'

export const authApi = {
  login: ({ tenant_slug, ...data }: LoginRequest): Promise<TokenResponse> =>
    apiClient
      .post<TokenResponse>('/auth/login', data, {
        headers: { 'X-Tenant-Slug': tenant_slug },
      })
      .then((res) => res.data),

  register: (data: RegisterRequest): Promise<TokenResponse> =>
    apiClient
      .post<TokenResponse>('/auth/register', data)
      .then((res) => res.data),

  refresh: (refreshToken: string): Promise<RefreshResponse> =>
    apiClient
      .post<RefreshResponse>('/auth/refresh', { refresh_token: refreshToken })
      .then((res) => res.data),

  logout: (refreshToken: string): Promise<void> =>
    apiClient
      .post<void>('/auth/logout', { refresh_token: refreshToken })
      .then(() => undefined),

  setupMFA: (): Promise<MFASetupResponse> =>
    apiClient
      .post<MFASetupResponse>('/auth/mfa/setup')
      .then((res) => res.data),

  verifyMFA: (code: string): Promise<MFAVerifyResponse> =>
    apiClient
      .post<MFAVerifyResponse>('/auth/mfa/verify', { code })
      .then((res) => res.data),
}
