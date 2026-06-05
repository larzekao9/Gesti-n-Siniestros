import { api } from './client'
import type { NotificationListResponse, Notification } from '@/types/notification'

export async function listNotifications(
  page = 1,
  limit = 20
): Promise<NotificationListResponse> {
  const { data } = await api.get('/me/notifications', { params: { page, limit } })
  return data
}

export async function markRead(id: string): Promise<Notification> {
  const { data } = await api.patch(`/me/notifications/${id}`)
  return data
}

export async function markAllRead(): Promise<void> {
  await api.post('/me/notifications/mark-all-read')
}
