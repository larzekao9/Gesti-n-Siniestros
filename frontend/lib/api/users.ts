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

export const usersApi = {
  list: (params?: { page?: number; limit?: number; role?: string; search?: string }): Promise<UserListResponse> =>
    apiClient.get<UserListResponse>('/users', { params }).then((r) => r.data),

  get: (id: string): Promise<User> =>
    apiClient.get<User>(`/users/${id}`).then((r) => r.data),

  create: (data: UserCreatePayload): Promise<User> =>
    apiClient.post<User>('/users', data).then((r) => r.data),

  update: (id: string, data: UserUpdatePayload): Promise<User> =>
    apiClient.patch<User>(`/users/${id}`, data).then((r) => r.data),
}
