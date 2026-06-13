import apiClient from './client'
import type { AIAnalysisListResponse } from '@/types/ai-analysis'

// CU-32: consultar resultado del análisis inteligente
export const aiAnalysesApi = {
  listForClaim: (claimId: string): Promise<AIAnalysisListResponse> =>
    apiClient.get<AIAnalysisListResponse>(`/claims/${claimId}/ai-analyses`).then((r) => r.data),

  // Solo supervisor/admin (403 para analista)
  refresh: (claimId: string): Promise<{ detail: string; enqueued: boolean }> =>
    apiClient.post(`/claims/${claimId}/ai-analyses/refresh`).then((r) => r.data),
}
