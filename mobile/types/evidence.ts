// ★ Espejo parcial de /frontend/types/evidence.ts (canal asegurado).

export type EvidenceType =
  | 'photo'
  | 'video'
  | 'invoice'
  | 'technical_report'
  | 'sketch'
  | 'police_report'
  | 'personal_doc'
  | 'other'

export interface Evidence {
  id: string
  tenant_id: string
  claim_request_id: string | null
  claim_id: string | null
  type: string
  file_url: string
  download_url: string | null
  file_name: string
  mime_type: string
  file_size: number
  created_at: string
}

export interface PresignedUrlResponse {
  upload_url: string
  s3_key: string
  expires_in: number
}

export interface EvidenceListResponse {
  items: Evidence[]
  total: number
  page: number
  limit: number
}
