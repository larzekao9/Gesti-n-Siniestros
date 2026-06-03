export interface User {
  id: string
  email: string
  full_name: string
  role: 'admin' | 'supervisor' | 'analyst'
  is_active?: boolean
  mfa_enabled: boolean
  tenant_id: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
  mfa_required?: boolean
}

export interface LoginRequest {
  email: string
  password: string
  tenant_slug: string
  mfa_code?: string
}

export interface RegisterRequest {
  email: string
  password: string
  full_name: string
  tenant_slug: string
}

export interface MFASetupResponse {
  secret: string
  qr_uri: string
}

export interface MFAVerifyResponse {
  message: string
}

export interface RefreshResponse {
  access_token: string
}

export interface ApiError {
  detail: string
  status_code?: number
}
