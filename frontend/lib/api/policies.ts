import apiClient from './client'

export interface Policy {
  id: string
  policy_number: string
  policyholder_id: string
  valid_from: string
  valid_to: string
  coverage_type: string
  exclusions: string | null
  status: string
  tenant_id: string
  created_at: string
  updated_at: string | null
}

export interface PolicyListResponse {
  items: Policy[]
  total: number
  page: number
  limit: number
}

export interface PolicyCreatePayload {
  policy_number: string
  policyholder_id: string
  valid_from: string
  valid_to: string
  coverage_type: string
  exclusions?: string | null
}

export interface PolicyUpdatePayload {
  policy_number?: string
  valid_from?: string
  valid_to?: string
  coverage_type?: string
  exclusions?: string | null
  status?: string
}

export const policiesApi = {
  list: (params?: { page?: number; limit?: number; policyholder_id?: string; search?: string }): Promise<PolicyListResponse> =>
    apiClient.get<PolicyListResponse>('/policies', { params }).then((r) => r.data),

  get: (id: string): Promise<Policy> =>
    apiClient.get<Policy>(`/policies/${id}`).then((r) => r.data),

  create: (data: PolicyCreatePayload): Promise<Policy> =>
    apiClient.post<Policy>('/policies', data).then((r) => r.data),

  update: (id: string, data: PolicyUpdatePayload): Promise<Policy> =>
    apiClient.patch<Policy>(`/policies/${id}`, data).then((r) => r.data),
}
