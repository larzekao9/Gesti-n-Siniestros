// ★ Espejo de /frontend/types + tipos propios del canal asegurado (Ciclo 7).
// Mantener sincronizado vía PR review (decisión §6.7.3 de Context.md).

export interface Account {
  id: string
  email: string
  policyholder_id: string
  tenant_id: string
  is_active: boolean
  mfa_enabled: boolean
}

export interface InsuredTokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  account: Account
}

export interface InsuredAccessTokenResponse {
  access_token: string
  token_type: string
}
