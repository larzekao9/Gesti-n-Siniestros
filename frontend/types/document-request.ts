export interface DocumentRequest {
  id: string
  tenant_id: string
  claim_id: string
  requested_by_user_id: string
  description: string
  status: 'pending' | 'submitted' | 'waived'
  resolved_at: string | null
  created_at: string
  updated_at: string | null
}

export interface DocumentRequestListResponse {
  items: DocumentRequest[]
  total: number
  page: number
  limit: number
}

export interface DocumentRequestCreatePayload {
  description: string
}
