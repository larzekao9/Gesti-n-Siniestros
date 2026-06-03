'use client'

import { Download } from 'lucide-react'

import { actionLabel } from '@/lib/api/audit'
import type { AuditLog } from '@/types/audit'
import { Button } from '@/components/ui/button'

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString('es-BO', {
    dateStyle: 'short',
    timeStyle: 'short',
  })
}

function exportCsv(logs: AuditLog[]) {
  const header = ['fecha', 'accion', 'entidad', 'entity_id', 'actor', 'ip']
  const rows = logs.map((l) => [
    l.created_at,
    l.action,
    l.entity_type,
    l.entity_id ?? '',
    l.actor_user_id ?? '',
    l.ip_address ?? '',
  ])
  const csv = [header, ...rows]
    .map((r) => r.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(','))
    .join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `auditoria_${new Date().toISOString().slice(0, 10)}.csv`
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

export default function AuditTable({ logs }: { logs: AuditLog[] }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
        <h3 className="text-sm font-semibold text-slate-700">Eventos</h3>
        <Button
          variant="outline"
          size="sm"
          onClick={() => exportCsv(logs)}
          disabled={logs.length === 0}
        >
          <Download className="mr-2 h-4 w-4" />
          Exportar CSV
        </Button>
      </div>
      {logs.length === 0 ? (
        <p className="py-10 text-center text-sm text-slate-400">Sin eventos para los filtros aplicados.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-xs text-slate-500">
                <th className="px-4 py-2">Fecha</th>
                <th className="px-4 py-2">Acción</th>
                <th className="px-4 py-2">Entidad</th>
                <th className="px-4 py-2">Actor</th>
                <th className="px-4 py-2">IP</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((l) => (
                <tr key={l.id} className="border-b border-slate-100 last:border-0">
                  <td className="px-4 py-2 whitespace-nowrap text-slate-500">{formatDate(l.created_at)}</td>
                  <td className="px-4 py-2 font-medium text-slate-800">{actionLabel(l.action)}</td>
                  <td className="px-4 py-2 text-slate-600">{l.entity_type}</td>
                  <td className="px-4 py-2 text-slate-500">
                    {l.actor_user_id ? `${l.actor_user_id.slice(0, 8)}…` : 'Sistema'}
                  </td>
                  <td className="px-4 py-2 text-slate-400">{l.ip_address ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
