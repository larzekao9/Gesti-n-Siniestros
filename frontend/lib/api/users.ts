import apiClient from './client'
import type { User } from '@/types/auth'

export interface UserListResponse {
  items: User[]
  total: number
  page: number
  limit: number
}

export interface UserCreatePayload {
  email: string
  password: string
  full_name: string
  role: string
}

export interface UserUpdatePayload {
  full_name?: string
  role?: string
  is_active?: boolean
  password?: string
}

export interface UserMinimal {
  id: string
  full_name: string
  role: string
}

export const usersApi = {
  list: (params?: { page?: number; limit?: number; role?: string; search?: string }): Promise<UserListResponse> =>
    apiClient.get<UserListResponse>('/users', { params }).then((r) => r.data),

  // Disponible a cualquier usuario autenticado, devuelve vista mínima.
  // Para múltiples roles pasar `['supervisor', 'admin']`.
  // FastAPI espera `?role=supervisor&role=admin` (repeat), no `role[]=` (brackets).
  listByRole: (roles: string[]): Promise<UserMinimal[]> => {
    const qs = roles.map((r) => `role=${encodeURIComponent(r)}`).join('&')
    return apiClient.get<UserMinimal[]>(`/users/by-role?${qs}`).then((r) => r.data)
  },

  get: (id: string): Promise<User> =>
    apiClient.get<User>(`/users/${id}`).then((r) => r.data),

  create: (data: UserCreatePayload): Promise<User> =>
    apiClient.post<User>('/users', data).then((r) => r.data),

  update: (id: string, data: UserUpdatePayload): Promise<User> =>
    apiClient.patch<User>(`/users/${id}`, data).then((r) => r.data),
}
