import apiClient from './client'
import type { AuditFilters, AuditLogListResponse } from '@/types/audit'

export const auditApi = {
  list: (params?: AuditFilters): Promise<AuditLogListResponse> =>
    apiClient.get<AuditLogListResponse>('/audit-logs', { params }).then((r) => r.data),

  listForEntity: (
    entityType: string,
    entityId: string,
    params?: { page?: number; limit?: number }
  ): Promise<AuditLogListResponse> =>
    apiClient
      .get<AuditLogListResponse>('/audit-logs', {
        params: { entity_type: entityType, entity_id: entityId, ...params },
      })
      .then((r) => r.data),
}

// Etiquetas legibles de las acciones registradas en audit_logs.
export const ACTION_LABELS: Record<string, string> = {
  CREATE_CLAIM: 'Expediente creado',
  FORMALIZE: 'Expediente formalizado',
  STATE_CHANGE: 'Cambio de estado',
  REASSIGN_ANALYST: 'Analista reasignado',
  ESCALATE: 'Escalado a supervisor',
  DECIDE: 'Decisión tomada',
  CREATE_OBSERVATION: 'Observación agregada',
  CREATE_THIRD_PARTY: 'Tercero agregado',
  UPDATE_THIRD_PARTY: 'Tercero actualizado',
  DELETE_THIRD_PARTY: 'Tercero eliminado',
  UPLOAD_EVIDENCE: 'Evidencia subida',
  CREATE_DOCUMENT_REQUEST: 'Documentación solicitada',
  SUBMIT_DOCUMENT_REQUEST: 'Documentación entregada',
  WAIVE_DOCUMENT_REQUEST: 'Documentación eximida',
  CREATE_TRAFFIC_REPORT: 'Acta de tránsito creada',
  UPDATE_TRAFFIC_REPORT: 'Acta de tránsito actualizada',
  DELETE_TRAFFIC_REPORT: 'Acta de tránsito eliminada',
  CREATE_DRAFT: 'Borrador creado',
  TAKE_REQUEST: 'Solicitud tomada',
  RELEASE_REQUEST: 'Solicitud liberada',
  REASSIGN_REQUEST: 'Solicitud reasignada',
  REJECT_AT_INTAKE: 'Rechazada en intake',
  REPORT_GENERATE: 'Reporte generado',
}

export function actionLabel(action: string): string {
  return ACTION_LABELS[action] ?? action
}
