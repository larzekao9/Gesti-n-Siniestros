import apiClient from './client'
import type {
  Claim,
  ClaimListResponse,
  ClaimCreatePayload,
  ClaimStatusUpdatePayload,
} from '@/types/claim'
import type {
  Observation,
  ObservationListResponse,
  ObservationCreatePayload,
} from '@/types/observation'
import type {
  ThirdParty,
  ThirdPartyListResponse,
  ThirdPartyCreatePayload,
  ThirdPartyUpdatePayload,
} from '@/types/third-party'

export const claimsApi = {
  list: (params?: {
    q?: string
    status?: string
    from?: string
    to?: string
    analyst?: string
    policyholder?: string
    page?: number
    limit?: number
  }): Promise<ClaimListResponse> =>
    apiClient.get<ClaimListResponse>('/claims', { params }).then((r) => r.data),

  get: (id: string): Promise<Claim> =>
    apiClient.get<Claim>(`/claims/${id}`).then((r) => r.data),

  create: (data: ClaimCreatePayload): Promise<Claim> =>
    apiClient.post<Claim>('/claims', data).then((r) => r.data),

  updateStatus: (id: string, data: ClaimStatusUpdatePayload): Promise<Claim> =>
    apiClient.patch<Claim>(`/claims/${id}/status`, data).then((r) => r.data),

  // Observations
  listObservations: (claimId: string, params?: { page?: number; limit?: number }): Promise<ObservationListResponse> =>
    apiClient.get<ObservationListResponse>(`/claims/${claimId}/observations`, { params }).then((r) => r.data),

  createObservation: (claimId: string, data: ObservationCreatePayload): Promise<Observation> =>
    apiClient.post<Observation>(`/claims/${claimId}/observations`, data).then((r) => r.data),

  // Third parties
  listThirdParties: (claimId: string, params?: { page?: number; limit?: number }): Promise<ThirdPartyListResponse> =>
    apiClient.get<ThirdPartyListResponse>(`/claims/${claimId}/third-parties`, { params }).then((r) => r.data),

  createThirdParty: (claimId: string, data: ThirdPartyCreatePayload): Promise<ThirdParty> =>
    apiClient.post<ThirdParty>(`/claims/${claimId}/third-parties`, data).then((r) => r.data),

  updateThirdParty: (claimId: string, tpId: string, data: ThirdPartyUpdatePayload): Promise<ThirdParty> =>
    apiClient.put<ThirdParty>(`/claims/${claimId}/third-parties/${tpId}`, data).then((r) => r.data),

  deleteThirdParty: (claimId: string, tpId: string): Promise<void> =>
    apiClient.delete(`/claims/${claimId}/third-parties/${tpId}`).then(() => undefined),
}
