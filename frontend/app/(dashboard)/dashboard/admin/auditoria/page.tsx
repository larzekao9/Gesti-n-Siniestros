'use client'

import { useCallback, useEffect, useState } from 'react'
import { toast } from 'sonner'

import { auditApi } from '@/lib/api/audit'
import type { AuditFilters as Filters, AuditLog } from '@/types/audit'
import AuditFilters from '@/components/audit/AuditFilters'
import AuditTable from '@/components/audit/AuditTable'
import { Button } from '@/components/ui/button'

const LIMIT = 50

export default function AuditoriaPage() {
  const [filters, setFilters] = useState<Filters>({})
  const [page, setPage] = useState(1)
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await auditApi.list({ ...filters, page, limit: LIMIT })
      setLogs(res.items)
      setTotal(res.total)
    } catch {
      toast.error('Error al cargar la bitácora de auditoría')
    } finally {
      setLoading(false)
    }
  }, [filters, page])

  useEffect(() => {
    load()
  }, [load])

  const patch = (p: Partial<Filters>) => {
    setPage(1)
    setFilters((f) => ({ ...f, ...p }))
  }

  const totalPages = Math.max(1, Math.ceil(total / LIMIT))

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Bitácora de auditoría</h1>
        <p className="mt-1 text-slate-500">
          Trazabilidad completa de las acciones del sistema (RNF de auditoría).
        </p>
      </div>

      <AuditFilters
        filters={filters}
        onChange={patch}
        onClear={() => {
          setPage(1)
          setFilters({})
        }}
      />

      {loading && logs.length === 0 ? (
        <p className="py-16 text-center text-slate-400">Cargando…</p>
      ) : (
        <>
          <AuditTable logs={logs} />
          <div className="flex items-center justify-between text-sm text-slate-500">
            <span>
              {total} evento{total === 1 ? '' : 's'} · página {page} de {totalPages}
            </span>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
              >
                Anterior
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
              >
                Siguiente
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
