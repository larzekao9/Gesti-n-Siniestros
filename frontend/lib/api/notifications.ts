import apiClient from './client'
import type { Notification, NotificationListResponse } from '@/types/notification'

export const notificationsApi = {
  list: (params?: {
    unread_only?: boolean
    page?: number
    limit?: number
  }): Promise<NotificationListResponse> =>
    apiClient
      .get<NotificationListResponse>('/me/notifications', { params })
      .then((r) => r.data),

  markRead: (id: string): Promise<Notification> =>
    apiClient
      .patch<Notification>(`/me/notifications/${id}`)
      .then((r) => r.data),

  markAllRead: (): Promise<{ marked_read: number }> =>
    apiClient
      .post<{ marked_read: number }>('/me/notifications/mark-all-read')
      .then((r) => r.data),
}
