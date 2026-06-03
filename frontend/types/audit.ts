// Tipos para la bitácora de auditoría (CU-31). Espejo de
// backend/app/schemas/audit.py.

export interface AuditLog {
  id: string
  actor_user_id: string | null
  action: string
  entity_type: string
  entity_id: string | null
  payload_diff: Record<string, unknown> | null
  ip_address: string | null
  user_agent: string | null
  tenant_id: string
  created_at: string
}

export interface AuditLogListResponse {
  items: AuditLog[]
  total: number
  page: number
  limit: number
}

export interface AuditFilters {
  entity_type?: string
  entity_id?: string
  actor?: string
  action?: string
  from?: string
  to?: string
  page?: number
  limit?: number
}
