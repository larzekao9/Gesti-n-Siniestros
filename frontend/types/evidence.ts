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
  metadata: Record<string, unknown> | null
  uploaded_by_user_id: string | null
  document_request_id: string | null
  created_at: string
  updated_at: string | null
}

export interface EvidenceListResponse {
  items: Evidence[]
  total: number
  page: number
  limit: number
}

export interface PresignedUrlRequest {
  subject_type: 'claim' | 'claim_request'
  subject_id: string
  type: string
  file_name: string
  mime_type: string
  file_size: number
}

export interface PresignedUrlResponse {
  upload_url: string
  s3_key: string
  expires_in: number
}

export interface EvidenceRegisterPayload {
  subject_type: 'claim' | 'claim_request'
  subject_id: string
  s3_key: string
  type: string
  file_name: string
  mime_type: string
  file_size: number
  metadata?: Record<string, unknown> | null
  document_request_id?: string | null
}

export interface EvidenceDownloadUrlResponse {
  download_url: string
  expires_in: number
}
