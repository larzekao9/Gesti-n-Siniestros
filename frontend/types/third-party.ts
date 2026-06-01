export interface ThirdParty {
  id: string
  claim_id: string
  kind: string
  full_name: string
  document_id: string | null
  contact_phone: string | null
  vehicle_plate: string | null
  vehicle_info: string | null
  statement: string | null
  tenant_id: string
  created_at: string
  updated_at: string | null
}

export interface ThirdPartyListResponse {
  items: ThirdParty[]
  total: number
  page: number
  limit: number
}

export interface ThirdPartyCreatePayload {
  kind: string
  full_name: string
  document_id?: string
  contact_phone?: string
  vehicle_plate?: string
  vehicle_info?: string
  statement?: string
}

export interface ThirdPartyUpdatePayload {
  kind?: string
  full_name?: string
  document_id?: string
  contact_phone?: string
  vehicle_plate?: string
  vehicle_info?: string
  statement?: string
}
