import apiClient from './client'

export interface Policyholder {
  id: string
  document_id: string
  full_name: string
  phone: string
  email: string | null
  address: string | null
  status: string
  tenant_id: string
  created_at: string
  updated_at: string | null
}

export interface PolicyholderListResponse {
  items: Policyholder[]
  total: number
  page: number
  limit: number
}

export interface PolicyholderCreatePayload {
  document_id: string
  full_name: string
  phone: string
  email?: string | null
  address?: string | null
}

export interface PolicyholderUpdatePayload {
  full_name?: string
  phone?: string
  email?: string | null
  address?: string | null
  status?: string
}

export const policyholdersApi = {
  list: (params?: { page?: number; limit?: number; search?: string }): Promise<PolicyholderListResponse> =>
    apiClient.get<PolicyholderListResponse>('/policyholders', { params }).then((r) => r.data),

  get: (id: string): Promise<Policyholder> =>
    apiClient.get<Policyholder>(`/policyholders/${id}`).then((r) => r.data),

  create: (data: PolicyholderCreatePayload): Promise<Policyholder> =>
    apiClient.post<Policyholder>('/policyholders', data).then((r) => r.data),

  update: (id: string, data: PolicyholderUpdatePayload): Promise<Policyholder> =>
    apiClient.patch<Policyholder>(`/policyholders/${id}`, data).then((r) => r.data),
}
