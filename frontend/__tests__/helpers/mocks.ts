/**
 * Shared mock factories for auth tests.
 */
import type { User, TokenResponse } from '@/types/auth'

export function mockUser(overrides: Partial<User> = {}): User {
  return {
    id: 'usr_01',
    email: 'analista@empresa.com',
    full_name: 'Ana Pérez',
    role: 'analyst',
    mfa_enabled: false,
    tenant_id: 'tenant_01',
    ...overrides,
  }
}

export function mockTokenResponse(overrides: Partial<TokenResponse> = {}): TokenResponse {
  return {
    access_token: 'access.jwt.token',
    refresh_token: 'refresh.jwt.token',
    token_type: 'bearer',
    user: mockUser(),
    ...overrides,
  }
}
