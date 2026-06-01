'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { DataTable, type Column } from '@/components/ui/data-table'
import { claimRequestsApi } from '@/lib/api/claim-requests'
import type { ClaimRequest } from '@/types/claim-request'

const LIMIT = 20

const STATUS_MAP: Record<string, { label: string; color: string }> = {
  draft: { label: 'Borrador', color: 'bg-gray-100 text-gray-700' },
  submitted: { label: 'Enviada', color: 'bg-blue-100 text-blue-700' },
  under_intake_review: { label: 'En revisión', color: 'bg-yellow-100 text-yellow-700' },
  formalized: { label: 'Formalizada', color: 'bg-green-100 text-green-700' },
  rejected_at_intake: { label: 'Rechazada', color: 'bg-red-100 text-red-700' },
}

export default function SolicitudesPage() {
  const router = useRouter()
  const [data, setData] = useState<ClaimRequest[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [takingId, setTakingId] = useState<string | null>(null)
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>()

  const handleSearchChange = (value: string) => {
    setSearch(value)
    if (timeoutRef.current) clearTimeout(timeoutRef.current)
    timeoutRef.current = setTimeout(() => setDebouncedSearch(value), 300)
  }

  const fetchData = useCallback(async () => {
    setIsLoading(true)
    try {
      const result = await claimRequestsApi.list({
        page,
        limit: LIMIT,
        q: debouncedSearch || undefined,
        status: statusFilter || undefined,
      })
      setData(result.items)
      setTotal(result.total)
    } catch {
      toast.error('Error al cargar las solicitudes')
    } finally {
      setIsLoading(false)
    }
  }, [page, debouncedSearch, statusFilter])

  useEffect(() => { fetchData() }, [fetchData])
  useEffect(() => { setPage(1) }, [debouncedSearch, statusFilter])

  const handleTake = async (id: string) => {
    setTakingId(id)
    try {
      await claimRequestsApi.take(id)
      toast.success('Solicitud tomada')
      fetchData()
    } catch {
      toast.error('Error al tomar la solicitud')
    } finally {
      setTakingId(null)
    }
  }

  const columns: Column<ClaimRequest>[] = [
    { header: 'Número', accessor: (r) => r.request_number || '—' },
    {
      header: 'Estado',
      accessor: (r) => {
        const s = STATUS_MAP[r.status] || { label: r.status, color: 'bg-gray-100 text-gray-700' }
        return <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${s.color}`}>{s.label}</span>
      },
    },
    { header: 'Fecha accidente', accessor: (r) => r.accident_date || '—' },
    { header: 'Ubicación', accessor: (r) => r.accident_location || '—' },
    {
      header: 'Acciones',
      accessor: (r) => (
        <div className="flex gap-2">
          <Button size="sm" variant="outline" onClick={() => router.push(`/dashboard/solicitudes/${r.id}`)}>
            Ver
          </Button>
          {r.status === 'submitted' && (
            <Button size="sm" onClick={() => handleTake(r.id)} disabled={takingId === r.id}>
              {takingId === r.id ? '...' : 'Tomar'}
            </Button>
          )}
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Solicitudes</h1>
      </div>

      <div className="flex gap-3 flex-wrap">
        <Input
          placeholder="Buscar solicitudes..."
          value={search}
          onChange={(e) => handleSearchChange(e.target.value)}
          className="max-w-xs"
        />
        <select
          className="border rounded-md px-3 py-2 text-sm"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="">Todos los estados</option>
          {Object.entries(STATUS_MAP).map(([k, v]) => (
            <option key={k} value={k}>{v.label}</option>
          ))}
        </select>
      </div>

      <DataTable
        columns={columns}
        data={data}
        isLoading={isLoading}
        total={total}
        page={page}
        limit={LIMIT}
        onPageChange={setPage}
        getRowKey={(r) => r.id}
      />
    </div>
  )
}
