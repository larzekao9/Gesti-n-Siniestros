'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { toast } from 'sonner'
import { Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { DataTable, type Column } from '@/components/ui/data-table'
import { claimsApi } from '@/lib/api/claims'
import type { Claim } from '@/types/claim'

const LIMIT = 20

const STATUS_MAP: Record<string, { label: string; color: string }> = {
  registered: { label: 'Registrado', color: 'bg-gray-100 text-gray-700' },
  in_review: { label: 'En revisión', color: 'bg-blue-100 text-blue-700' },
  observed: { label: 'Observado', color: 'bg-yellow-100 text-yellow-700' },
  docs_pending: { label: 'Docs pendientes', color: 'bg-orange-100 text-orange-700' },
  in_evaluation: { label: 'En evaluación', color: 'bg-purple-100 text-purple-700' },
  approved: { label: 'Aprobado', color: 'bg-green-100 text-green-700' },
  rejected: { label: 'Rechazado', color: 'bg-red-100 text-red-700' },
  closed: { label: 'Cerrado', color: 'bg-gray-200 text-gray-500' },
}

const SOURCE_MAP: Record<string, string> = {
  mobile_app: 'App móvil',
  internal: 'Interno',
}

export default function ExpedientesPage() {
  const router = useRouter()
  const [data, setData] = useState<Claim[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>()

  const handleSearchChange = (value: string) => {
    setSearch(value)
    if (timeoutRef.current) clearTimeout(timeoutRef.current)
    timeoutRef.current = setTimeout(() => setDebouncedSearch(value), 300)
  }

  const fetchData = useCallback(async () => {
    setIsLoading(true)
    try {
      const result = await claimsApi.list({
        page,
        limit: LIMIT,
        q: debouncedSearch || undefined,
        status: statusFilter || undefined,
      })
      setData(result.items)
      setTotal(result.total)
    } catch {
      toast.error('Error al cargar los expedientes')
    } finally {
      setIsLoading(false)
    }
  }, [page, debouncedSearch, statusFilter])

  useEffect(() => { fetchData() }, [fetchData])
  useEffect(() => { setPage(1) }, [debouncedSearch, statusFilter])

  const columns: Column<Claim>[] = [
    { header: 'Número', accessor: (r) => r.claim_number },
    {
      header: 'Estado',
      accessor: (r) => {
        const s = STATUS_MAP[r.status] ?? { label: r.status, color: 'bg-gray-100 text-gray-700' }
        return (
          <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${s.color}`}>
            {s.label}
          </span>
        )
      },
    },
    {
      header: 'Origen',
      accessor: (r) => (
        <span className="text-xs text-slate-500">
          {SOURCE_MAP[r.source] ?? r.source}
        </span>
      ),
    },
    {
      header: 'Fecha accidente',
      accessor: (r) =>
        r.accident_date
          ? new Date(r.accident_date + 'T00:00:00').toLocaleDateString('es-ES')
          : '—',
    },
    { header: 'Ubicación', accessor: (r) => r.accident_location || '—' },
    {
      header: '',
      accessor: (r) => (
        <Button
          size="sm"
          variant="outline"
          onClick={() => router.push(`/dashboard/expedientes/${r.id}`)}
        >
          Ver
        </Button>
      ),
      className: 'w-[80px]',
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Expedientes</h1>
        <Button onClick={() => router.push('/dashboard/expedientes/nuevo')}>
          <Plus className="h-4 w-4" />
          Nuevo Expediente
        </Button>
      </div>

      <div className="flex gap-3 flex-wrap">
        <Input
          placeholder="Buscar expedientes..."
          value={search}
          onChange={(e) => handleSearchChange(e.target.value)}
          className="max-w-xs"
        />
        <select
          className="border rounded-md px-3 py-2 text-sm bg-white"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="">Todos los estados</option>
          {Object.entries(STATUS_MAP).map(([k, v]) => (
            <option key={k} value={k}>
              {v.label}
            </option>
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
        emptyMessage="No se encontraron expedientes."
      />
    </div>
  )
}
