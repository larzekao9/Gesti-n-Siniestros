import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { listNotifications, markAllRead, markRead } from '../api/notifications'

const KEY = ['me', 'notifications'] as const

export function useNotifications() {
  return useQuery({
    queryKey: KEY,
    queryFn: () => listNotifications(1, 50),
    refetchInterval: 30000, // polling cada 30s (paridad con el web)
  })
}

export function useMarkRead() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => markRead(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  })
}

export function useMarkAllRead() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => markAllRead(),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  })
}
