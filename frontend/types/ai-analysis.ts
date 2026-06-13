// Ciclo 8 — CU-32: contratos de ai_analyses (espejo de schemas/ai_analysis.py)

export type AIAnalysisKind = 'inconsistency' | 'duplicate' | 'fraud_score' | 'damage_assessment'
export type AIAnalysisStatus = 'processing' | 'done' | 'error'

export interface InconsistencyFinding {
  severity: 'info' | 'warning' | 'critical'
  field: string
  message: string
}

export interface DuplicateMatch {
  claim_id: string
  claim_number: string
  similarity: number
}

export interface FraudFactor {
  name: string
  contribution: number
  direction: 'up' | 'down'
}

export interface DamageAssessment {
  damage_type: string
  severity: 'leve' | 'moderado' | 'severo' | 'indeterminado'
  confidence: number
}

export interface AIAnalysis {
  id: string
  claim_id: string | null
  claim_request_id: string | null
  evidence_id: string | null
  kind: AIAnalysisKind
  status: AIAnalysisStatus
  score: number | null
  // Forma según kind: {findings} | {matches} | {score, factors} | DamageAssessment
  payload: Record<string, unknown> | null
  explanation: string | null
  model_version: string | null
  created_at: string
  updated_at: string | null
}

export interface AIAnalysisListResponse {
  items: AIAnalysis[]
}
