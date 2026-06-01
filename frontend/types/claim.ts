export interface PolicyholderSnippet {
  id: string
  full_name: string
  document_id: string
  phone?: string | null
}

export interface PolicySnippet {
  id: string
  policy_number: string
  coverage_type: string
  valid_from: string
  valid_to: string
}

export interface VehicleSnippet {
  id: string
  plate: string
  make: string
  model: string
  year: number
}

export interface Claim {
  id: string
  claim_number: string
  claim_request_id: string | null
  policyholder_id: string
  policy_id: string
  vehicle_id: string
  policyholder?: PolicyholderSnippet | null
  policy?: PolicySnippet | null
  vehicle?: VehicleSnippet | null
  status: string
  source: string
  accident_date: string
  accident_time: string | null
  accident_location: string
  accident_lat: number | null
  accident_lng: number | null
  accident_description: string | null
  reported_damages: string | null
  created_by_user_id: string | null
  assigned_analyst_id: string | null
  supervisor_id: string | null
  fraud_score: number | null
  decision: string | null
  decision_reason: string | null
  decided_by_user_id: string | null
  decided_at: string | null
  tenant_id: string
  created_at: string
  updated_at: string | null
}

export interface ClaimListResponse {
  items: Claim[]
  total: number
  page: number
  limit: number
}

export interface ClaimCreatePayload {
  policyholder_id: string
  policy_id: string
  vehicle_id: string
  accident_date: string
  accident_time?: string
  accident_location: string
  accident_lat?: number
  accident_lng?: number
  accident_description?: string
  reported_damages?: string
}

export interface ClaimStatusUpdatePayload {
  new_status: string
  reason?: string
}

export interface FormalizeResponse {
  claim: Claim
  request: ClaimRequest | null
}

import type { ClaimRequest } from './claim-request'
