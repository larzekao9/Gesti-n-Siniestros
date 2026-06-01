import apiClient from './client'
import type {
  ClaimRequest,
  ClaimRequestListResponse,
  RejectIntakePayload,
  ReassignPayload,
} from '@/types/claim-request'
import type { FormalizeResponse } from '@/types/claim'

export const claimRequestsApi = {
  list: (params?: {
    q?: string
    status?: string
    from?: string
    to?: string
    page?: number
    limit?: number
  }): Promise<ClaimRequestListResponse> =>
    apiClient.get<ClaimRequestListResponse>('/claim-requests', { params }).then((r) => r.data),

  get: (id: string): Promise<ClaimRequest> =>
    apiClient.get<ClaimRequest>(`/claim-requests/${id}`).then((r) => r.data),

  take: (id: string): Promise<ClaimRequest> =>
    apiClient.post<ClaimRequest>(`/claim-requests/${id}/take`).then((r) => r.data),

  release: (id: string): Promise<ClaimRequest> =>
    apiClient.post<ClaimRequest>(`/claim-requests/${id}/release`).then((r) => r.data),

  reassign: (id: string, data: ReassignPayload): Promise<ClaimRequest> =>
    apiClient.post<ClaimRequest>(`/claim-requests/${id}/reassign`, data).then((r) => r.data),

  reject: (id: string, data: RejectIntakePayload): Promise<ClaimRequest> =>
    apiClient.post<ClaimRequest>(`/claim-requests/${id}/reject`, data).then((r) => r.data),

  formalize: (id: string): Promise<FormalizeResponse> =>
    apiClient.post<FormalizeResponse>(`/claim-requests/${id}/formalize`).then((r) => r.data),
}
