import apiClient from './client'
import type {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  MFASetupResponse,
  MFAVerifyResponse,
  RefreshResponse,
  User,
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

  getMe: (): Promise<User> =>
    apiClient
      .get<User>('/auth/me')
      .then((res) => res.data),

  requestPasswordReset: (email: string, tenant_slug: string): Promise<{ message: string }> =>
    apiClient
      .post<{ message: string }>('/auth/password-reset/request', { email, tenant_slug })
      .then((res) => res.data),

  confirmPasswordReset: (token: string, new_password: string): Promise<{ message: string }> =>
    apiClient
      .post<{ message: string }>('/auth/password-reset/confirm', { token, new_password })
      .then((res) => res.data),

  changePassword: (current_password: string, new_password: string, confirm_password: string): Promise<{ message: string }> =>
    apiClient
      .post<{ message: string }>('/auth/password-change', { current_password, new_password, confirm_password })
      .then((res) => res.data),
}
