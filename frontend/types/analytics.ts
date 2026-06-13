// Tipos para el dashboard de analytics (CU-21). Espejo de
// backend/app/schemas/analytics.py.

export interface KPIs {
  total_claims: number
  total_requests: number
  claims_by_status: Record<string, number>
  requests_by_status: Record<string, number>
  intake_rejection_rate: number
  approval_rate: number
  avg_days_to_decision: number | null
  open_claims: number
}

export interface StatusDistributionItem {
  status: string
  count: number
}

export interface StatusDistributionResponse {
  items: StatusDistributionItem[]
  total: number
}

export interface TimelinePoint {
  date: string
  count: number
}

export interface TimelineResponse {
  items: TimelinePoint[]
}

export interface CoverageDistributionItem {
  coverage_type: string
  count: number
}

export interface CoverageDistributionResponse {
  items: CoverageDistributionItem[]
  total: number
}

export interface AnalystProductivityItem {
  analyst_id: string
  analyst_name: string
  assigned: number
  decided: number
}

export interface AnalystProductivityResponse {
  items: AnalystProductivityItem[]
}

export interface AnalyticsFilters {
  from?: string
  to?: string
  analyst?: string
}

// Fase 2 de CU-21 (Ciclo 8): KPIs de IA.
export interface TopInconsistencyItem {
  field: string
  count: number
}

export interface AIKPIs {
  suspicious_claims: number
  scored_claims: number
  high_fraud_rate: number
  fraud_alert_threshold: number
  total_inconsistency_findings: number
  top_inconsistencies: TopInconsistencyItem[]
}
