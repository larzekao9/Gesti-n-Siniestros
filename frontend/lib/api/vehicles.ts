import apiClient from './client'

export interface Vehicle {
  id: string
  plate: string
  make: string
  model: string
  year: number
  color: string | null
  vehicle_type: string
  policy_id: string
  status: string
  tenant_id: string
  created_at: string
  updated_at: string | null
}

export interface VehicleListResponse {
  items: Vehicle[]
  total: number
  page: number
  limit: number
}

export interface VehicleCreatePayload {
  plate: string
  make: string
  model: string
  year: number
  color?: string | null
  vehicle_type?: string
  policy_id: string
}

export interface VehicleUpdatePayload {
  make?: string
  model?: string
  year?: number
  color?: string | null
  vehicle_type?: string
  policy_id?: string
  status?: string
}

export const vehiclesApi = {
  list: (params?: { page?: number; limit?: number; policy_id?: string; search?: string }): Promise<VehicleListResponse> =>
    apiClient.get<VehicleListResponse>('/vehicles', { params }).then((r) => r.data),

  get: (id: string): Promise<Vehicle> =>
    apiClient.get<Vehicle>(`/vehicles/${id}`).then((r) => r.data),

  create: (data: VehicleCreatePayload): Promise<Vehicle> =>
    apiClient.post<Vehicle>('/vehicles', data).then((r) => r.data),

  update: (id: string, data: VehicleUpdatePayload): Promise<Vehicle> =>
    apiClient.patch<Vehicle>(`/vehicles/${id}`, data).then((r) => r.data),
}
