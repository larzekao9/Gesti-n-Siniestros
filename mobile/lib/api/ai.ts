import { api } from './client'
import type { AIAnalysis } from '@/types/ai-analysis'

// CU-33: pide al backend el análisis de daño de una foto ya subida.
// La API key de OpenAI vive SOLO en el backend (ADR-012); la app nunca la ve.
export async function analyzeEvidenceDamage(
  requestId: string,
  evidenceId: string
): Promise<AIAnalysis> {
  const { data } = await api.post<AIAnalysis>(
    `/me/claim-requests/${requestId}/evidences/${evidenceId}/analyze-damage`
  )
  return data
}
