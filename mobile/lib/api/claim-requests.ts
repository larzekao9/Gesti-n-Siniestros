import { api } from './client'
import type {
  ClaimRequest,
  ClaimRequestCreatePayload,
  ClaimRequestUpdatePayload,
  InsuredClaimRequestListResponse,
} from '@/types/claim-request'
import type { ClaimInsured } from '@/types/claim'

export async function listMyClaimRequests(
  page = 1,
  limit = 20
): Promise<InsuredClaimRequestListResponse> {
  const { data } = await api.get('/me/claim-requests', { params: { page, limit } })
  return data
}

export async function getMyClaimRequest(id: string): Promise<ClaimRequest> {
  const { data } = await api.get(`/me/claim-requests/${id}`)
  return data
}

export async function createDraft(
  payload: ClaimRequestCreatePayload
): Promise<ClaimRequest> {
  const { data } = await api.post('/me/claim-requests', payload)
  return data
}

export async function updateDraft(
  id: string,
  payload: ClaimRequestUpdatePayload
): Promise<ClaimRequest> {
  const { data } = await api.patch(`/me/claim-requests/${id}`, payload)
  return data
}

export async function deleteDraft(id: string): Promise<void> {
  await api.delete(`/me/claim-requests/${id}`)
}

export async function submitClaimRequest(id: string): Promise<ClaimRequest> {
  const { data } = await api.post(`/me/claim-requests/${id}/submit`)
  return data
}

export async function getMyClaim(id: string): Promise<ClaimInsured> {
  const { data } = await api.get(`/me/claims/${id}`)
  return data
}
