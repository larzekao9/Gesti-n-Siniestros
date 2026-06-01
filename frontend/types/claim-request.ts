export interface ClaimRequest {
  id: string
  request_number: string | null
  status: string
  policyholder_id: string
  policy_id: string
  vehicle_id: string
  accident_date: string | null
  accident_time: string | null
  accident_location: string | null
  accident_lat: number | null
  accident_lng: number | null
  accident_description: string | null
  reported_damages: string | null
  submitted_at: string | null
  reviewed_by_user_id: string | null
  intake_decision_reason: string | null
  formalized_claim_id: string | null
  tenant_id: string
  created_at: string
  updated_at: string | null
}

export interface ClaimRequestListResponse {
  items: ClaimRequest[]
  total: number
  page: number
  limit: number
}

export interface RejectIntakePayload {
  reason: string
}

export interface ReassignPayload {
  target_user_id: string
}
