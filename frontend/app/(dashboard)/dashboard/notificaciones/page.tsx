'use client'

import { useState } from 'react'
import { useNotifications } from '@/lib/hooks/useNotifications'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { Bell, CheckCheck } from 'lucide-react'

const KIND_LABELS: Record<string, string> = {
  intake_rejected: 'Solicitud rechazada',
  docs_requested: 'Documentación solicitada',
  escalated: 'Expediente escalado',
  assigned: 'Expediente asignado',
  decision: 'Decisión de expediente',
  state_change: 'Cambio de estado',
  claim_created: 'Expediente creado',
}

export default function NotificationsPage() {
  const { notifications, unreadCount, total, loading, markRead, markAllRead, fetchNotifications } =
    useNotifications()
  const [page, setPage] = useState(1)
  const [unreadOnly, setUnreadOnly] = useState(false)
  const [processing, setProcessing] = useState(false)
  const limit = 20

  const totalPages = Math.ceil(total / limit)

  const handleMarkAllRead = async () => {
    setProcessing(true)
    await markAllRead()
    setProcessing(false)
  }

  const handleShowUnreadOnly = () => {
    setUnreadOnly(!unreadOnly)
    setPage(1)
    fetchNotifications(1, limit, !unreadOnly)
  }

  const handlePageChange = (newPage: number) => {
    setPage(newPage)
    fetchNotifications(newPage, limit, unreadOnly)
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Notificaciones</h1>
          <p className="text-sm text-slate-500 mt-1">
            {unreadCount} sin leer de {total} total
          </p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" size="sm" onClick={handleShowUnreadOnly}>
            {unreadOnly ? 'Mostrar todas' : 'Solo no leídas'}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleMarkAllRead}
            disabled={unreadCount === 0 || processing}
          >
            <CheckCheck className="h-4 w-4 mr-1.5" />
            Marcar todas leídas
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12 text-slate-500">
          <Bell className="h-8 w-8 mx-auto mb-3 text-slate-300" />
          Cargando notificaciones...
        </div>
      ) : notifications.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg border border-slate-200">
          <Bell className="h-10 w-10 mx-auto mb-3 text-slate-300" />
          <p className="text-slate-500 font-medium">Sin notificaciones</p>
          <p className="text-sm text-slate-400 mt-1">
            {unreadOnly
              ? 'No tenés notificaciones sin leer'
              : 'No tenés notificaciones todavía'}
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {notifications.map((n) => (
            <div
              key={n.id}
              className={cn(
                'p-4 bg-white rounded-lg border border-slate-200 hover:border-slate-300 transition-colors cursor-pointer',
                !n.read_at && 'border-l-4 border-l-blue-500 bg-blue-50/30'
              )}
              onClick={() => {
                if (!n.read_at) markRead(n.id)
              }}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-blue-600 bg-blue-100 rounded px-1.5 py-0.5">
                      {KIND_LABELS[n.kind] || n.kind}
                    </span>
                    {!n.read_at && (
                      <span className="h-2 w-2 rounded-full bg-blue-600 flex-shrink-0" />
                    )}
                  </div>
                  <p className="text-sm font-medium text-slate-800 mt-1.5">
                    {n.title}
                  </p>
                  <p className="text-sm text-slate-500 mt-0.5">{n.body}</p>
                </div>
                <span className="text-xs text-slate-400 flex-shrink-0">
                  {new Date(n.created_at).toLocaleString()}
                </span>
              </div>
            </div>
          ))}

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 pt-4">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => handlePageChange(page - 1)}
              >
                Anterior
              </Button>
              <span className="text-sm text-slate-500 px-3">
                {page} de {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => handlePageChange(page + 1)}
              >
                Siguiente
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
