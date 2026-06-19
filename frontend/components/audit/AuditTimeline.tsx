'use client'

import { useEffect, useState } from 'react'
import { History, ChevronDown, ChevronRight } from 'lucide-react'

import { auditApi, actionLabel } from '@/lib/api/audit'
import type { AuditLog } from '@/types/audit'

function formatDate(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleString('es-BO', { dateStyle: 'medium', timeStyle: 'short' })
}

/** Línea de tiempo de auditoría para una entidad (CU-31 vista por entidad). */
export default function AuditTimeline({
  entityType,
  entityId,
}: {
  entityType: string
  entityId: string
}) {
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [expanded, setExpanded] = useState<Set<string>>(new Set())

  useEffect(() => {
    let active = true
    setLoading(true)
    auditApi
      .listForEntity(entityType, entityId, { limit: 100 })
      .then((res) => {
        if (active) setLogs(res.items)
      })
      .catch(() => {
        if (active) setError(true)
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [entityType, entityId])

  const toggle = (id: string) =>
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })

  if (loading) return <p className="py-8 text-center text-slate-500">Cargando bitácora…</p>
  if (error) return <p className="py-8 text-center text-red-500">Error al cargar la bitácora</p>
  if (logs.length === 0)
    return (
      <p className="py-8 text-center text-slate-400">Sin eventos de auditoría para este expediente.</p>
    )

  return (
    <ol className="relative space-y-4 border-l border-slate-200 pl-6">
      {logs.map((log) => {
        const isOpen = expanded.has(log.id)
        const hasDiff = log.payload_diff && Object.keys(log.payload_diff).length > 0
        return (
          <li key={log.id} className="relative">
            <span className="absolute -left-[1.6rem] flex h-6 w-6 items-center justify-center rounded-full bg-blue-50 ring-4 ring-white">
              <History className="h-3 w-3 text-blue-600" />
            </span>
            <div className="rounded-lg border border-slate-200 bg-white p-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-slate-800">{actionLabel(log.action)}</span>
                <time className="text-xs text-slate-400">{formatDate(log.created_at)}</time>
              </div>
              <p className="mt-0.5 text-xs text-slate-500">
                {log.actor_user_id ? `Actor: ${log.actor_user_id.slice(0, 8)}…` : 'Sistema'}
                {log.ip_address ? ` · ${log.ip_address}` : ''}
              </p>
              {hasDiff && (
                <div className="mt-2">
                  <button
                    onClick={() => toggle(log.id)}
                    className="flex items-center gap-1 text-xs font-medium text-blue-600 hover:underline"
                  >
                    {isOpen ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
                    {isOpen ? 'Ocultar detalle' : 'Ver detalle'}
                  </button>
                  {isOpen && (
                    <pre className="mt-2 overflow-x-auto rounded bg-slate-50 p-2 text-xs text-slate-600">
                      {JSON.stringify(log.payload_diff, null, 2)}
                    </pre>
                  )}
                </div>
              )}
            </div>
          </li>
        )
      })}
    </ol>
  )
}
