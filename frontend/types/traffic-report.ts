export interface TrafficReport {
  id: string
  tenant_id: string
  claim_id: string
  evidence_id: string | null
  officer_name: string | null
  report_code: string | null
  jurisdiction: string | null
  report_date: string | null
  summary: string | null
  created_at: string
  updated_at: string | null
}

export interface TrafficReportListResponse {
  items: TrafficReport[]
  total: number
  page: number
  limit: number
}

export interface TrafficReportCreatePayload {
  evidence_id?: string | null
  officer_name?: string | null
  report_code?: string | null
  jurisdiction?: string | null
  report_date?: string | null
  summary?: string | null
}

export interface TrafficReportUpdatePayload {
  evidence_id?: string | null
  officer_name?: string | null
  report_code?: string | null
  jurisdiction?: string | null
  report_date?: string | null
  summary?: string | null
}
