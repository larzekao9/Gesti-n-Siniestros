// ★ Espejo parcial de /frontend/types/ai-analysis.ts (canal asegurado).
// Ciclo 8 Sub-entrega B — CU-33: análisis de daño por foto.

export type AIAnalysisStatus = 'processing' | 'done' | 'error'

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
  kind: string
  status: AIAnalysisStatus
  score: number | null
  payload: Record<string, unknown> | null
  explanation: string | null
  model_version: string | null
  created_at: string
  updated_at: string | null
}
