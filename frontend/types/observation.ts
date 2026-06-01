export interface Observation {
  id: string
  claim_id: string
  author_user_id: string | null
  comment: string
  is_internal: boolean
  tenant_id: string
  created_at: string
  updated_at: string | null
}

export interface ObservationListResponse {
  items: Observation[]
  total: number
  page: number
  limit: number
}

export interface ObservationCreatePayload {
  comment: string
  is_internal: boolean
}
