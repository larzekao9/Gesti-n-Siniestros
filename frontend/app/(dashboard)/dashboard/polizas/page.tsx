'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { DataTable, type Column } from '@/components/ui/data-table'
import { PolicyFormDialog } from '@/components/policies/PolicyFormDialog'
import { policiesApi, type Policy } from '@/lib/api/policies'

const LIMIT = 20

export default function PolizasPage() {
  const [data, setData] = useState<Policy[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<Policy | null>(null)
  const [togglingId, setTogglingId] = useState<string | null>(null)
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>()

  const handleSearchChange = (value: string) => {
    setSearch(value)
    if (timeoutRef.current) clearTimeout(timeoutRef.current)
    timeoutRef.current = setTimeout(() => {
      setDebouncedSearch(value)
    }, 300)
  }

  const fetchData = useCallback(async () => {
    setIsLoading(true)
    try {
      const result = await policiesApi.list({
        page,
        limit: LIMIT,
        search: debouncedSearch || undefined,
      })
      setData(result.items)
      setTotal(result.total)
    } catch {
      toast.error('Error al cargar las pólizas')
    } finally {
      setIsLoading(false)
    }
  }, [page, debouncedSearch])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  useEffect(() => {
    setPage(1)
  }, [debouncedSearch])

  const handleOpenCreate = () => {
    setEditingItem(null)
    setIsFormOpen(true)
  }

  const handleOpenEdit = (row: Policy) => {
    setEditingItem(row)
    setIsFormOpen(true)
  }

  const handleCloseForm = () => {
    setIsFormOpen(false)
    setEditingItem(null)
  }

  const handleToggleStatus = async (row: Policy) => {
    const targetStatus = row.status === 'active' ? 'inactive' : 'active'
    const confirmMsg =
      targetStatus === 'inactive'
        ? `¿Desactivar la póliza "${row.policy_number}"?`
        : `¿Reactivar la póliza "${row.policy_number}"?`
    if (!window.confirm(confirmMsg)) return
    setTogglingId(row.id)
    try {
      await policiesApi.update(row.id, { status: targetStatus })
      toast.success(
        targetStatus === 'inactive' ? 'Póliza desactivada' : 'Póliza reactivada',
      )
      fetchData()
    } catch {
      toast.error('No se pudo cambiar el estado')
    } finally {
      setTogglingId(null)
    }
  }

  const columns: Column<Policy>[] = [
    { header: 'Número', accessor: 'policy_number' },
    { header: 'Cobertura', accessor: 'coverage_type' },
    {
      header: 'Vigencia',
      accessor: (row) =>
        `${new Date(row.valid_from).toLocaleDateString('es-CO')} — ${new Date(row.valid_to).toLocaleDateString('es-CO')}`,
    },
    {
      header: 'Estado',
      accessor: (row) => (
        <span
          className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
            row.status === 'active'
              ? 'bg-green-100 text-green-700'
              : row.status === 'expired'
                ? 'bg-red-100 text-red-700'
                : 'bg-slate-100 text-slate-600'
          }`}
        >
          {row.status}
        </span>
      ),
    },
    {
      header: 'Acciones',
      accessor: (row) => (
        <div className="flex gap-1">
          <Button variant="ghost" size="sm" onClick={() => handleOpenEdit(row)}>
            Editar
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className={
              row.status === 'active'
                ? 'text-red-600 hover:text-red-700 hover:bg-red-50'
                : 'text-green-600 hover:text-green-700 hover:bg-green-50'
            }
            onClick={() => handleToggleStatus(row)}
            disabled={togglingId === row.id || row.status === 'expired'}
            title={
              row.status === 'expired'
                ? 'La póliza está vencida — no se puede reactivar.'
                : undefined
            }
          >
            {togglingId === row.id
              ? '…'
              : row.status === 'active'
                ? 'Desactivar'
                : 'Reactivar'}
          </Button>
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Pólizas</h1>
          <p className="text-slate-500 mt-1">Gestión de pólizas vehiculares</p>
        </div>
        <Button onClick={handleOpenCreate}>Nueva Póliza</Button>
      </div>

      <Input
        placeholder="Buscar por número de póliza..."
        value={search}
        onChange={(e) => handleSearchChange(e.target.value)}
        className="max-w-sm"
      />

      <DataTable
        columns={columns}
        data={data}
        page={page}
        total={total}
        limit={LIMIT}
        onPageChange={setPage}
        isLoading={isLoading}
        emptyMessage="No se encontraron pólizas."
        getRowKey={(row) => row.id}
      />

      <PolicyFormDialog
        open={isFormOpen}
        onClose={handleCloseForm}
        onSuccess={fetchData}
        initialData={editingItem}
      />
    </div>
  )
}
