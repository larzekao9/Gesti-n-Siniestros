// Vista del expediente para el asegurado (espejo de ClaimOutInsured del backend).

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

export interface PublicObservation {
  id: string
  comment: string
  created_at: string
}

export interface InsuredDocumentRequest {
  id: string
  description: string
  status: string
  created_at: string
  resolved_at: string | null
}

export interface InsuredTimelineEntry {
  to_status: string
  created_at: string
}

export interface ClaimInsured {
  id: string
  claim_number: string
  status: string
  source: string
  accident_date: string
  accident_time: string | null
  accident_location: string
  accident_lat: number | null
  accident_lng: number | null
  accident_description: string | null
  reported_damages: string | null
  decision: string | null
  decision_reason: string | null
  decided_at: string | null
  created_at: string
  updated_at: string | null
  policyholder: PolicyholderSnippet | null
  policy: PolicySnippet | null
  vehicle: VehicleSnippet | null
  observations: PublicObservation[]
  document_requests: InsuredDocumentRequest[]
  timeline: InsuredTimelineEntry[]
}
