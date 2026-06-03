'use client'

import { useState, useEffect, useCallback } from 'react'
import { notificationsApi } from '@/lib/api/notifications'
import type { Notification, NotificationListResponse } from '@/types/notification'

const POLL_INTERVAL_MS = 30_000

export function useNotifications() {
  const [data, setData] = useState<NotificationListResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchNotifications = useCallback(
    async (page = 1, limit = 10, unreadOnly = false) => {
      try {
        setLoading(true)
        const res = await notificationsApi.list({ page, limit, unread_only: unreadOnly })
        setData(res)
        setError(null)
      } catch (err) {
        setError('Error al cargar notificaciones')
      } finally {
        setLoading(false)
      }
    },
    []
  )

  useEffect(() => {
    fetchNotifications()
    const interval = setInterval(() => {
      fetchNotifications(1, 10)
    }, POLL_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [fetchNotifications])

  const markRead = async (id: string) => {
    await notificationsApi.markRead(id)
    setData((prev) => {
      if (!prev) return prev
      return {
        ...prev,
        unread_count: Math.max(0, prev.unread_count - 1),
        items: prev.items.map((n) =>
          n.id === id ? { ...n, read_at: new Date().toISOString() } : n
        ),
      }
    })
  }

  const markAllRead = async () => {
    await notificationsApi.markAllRead()
    setData((prev) => {
      if (!prev) return prev
      return {
        ...prev,
        unread_count: 0,
        items: prev.items.map((n) => ({ ...n, read_at: n.read_at || new Date().toISOString() })),
      }
    })
  }

  return {
    notifications: data?.items ?? [],
    unreadCount: data?.unread_count ?? 0,
    total: data?.total ?? 0,
    loading,
    error,
    fetchNotifications,
    markRead,
    markAllRead,
  }
}
