import apiClient from './client'
import type {
  DocumentRequest,
  DocumentRequestListResponse,
  DocumentRequestCreatePayload,
} from '@/types/document-request'

export const documentRequestsApi = {
  listForClaim: (claimId: string, params?: { page?: number; limit?: number }): Promise<DocumentRequestListResponse> =>
    apiClient.get<DocumentRequestListResponse>('/document-requests', { params: { claim_id: claimId, ...params } }).then((r) => r.data),

  create: (claimId: string, data: DocumentRequestCreatePayload): Promise<DocumentRequest> =>
    apiClient.post<DocumentRequest>(`/document-requests?claim_id=${claimId}`, data).then((r) => r.data),

  submit: (requestId: string): Promise<DocumentRequest> =>
    apiClient.post<DocumentRequest>(`/document-requests/${requestId}/submit`).then((r) => r.data),

  waive: (requestId: string): Promise<DocumentRequest> =>
    apiClient.post<DocumentRequest>(`/document-requests/${requestId}/waive`).then((r) => r.data),
}
