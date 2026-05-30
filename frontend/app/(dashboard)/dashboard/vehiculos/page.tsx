'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { DataTable, type Column } from '@/components/ui/data-table'
import { VehicleFormDialog } from '@/components/vehicles/VehicleFormDialog'
import { vehiclesApi, type Vehicle } from '@/lib/api/vehicles'

const LIMIT = 20

export default function VehiculosPage() {
  const [data, setData] = useState<Vehicle[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<Vehicle | null>(null)
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
      const result = await vehiclesApi.list({
        page,
        limit: LIMIT,
        search: debouncedSearch || undefined,
      })
      setData(result.items)
      setTotal(result.total)
    } catch {
      toast.error('Error al cargar los vehículos')
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

  const handleOpenEdit = (row: Vehicle) => {
    setEditingItem(row)
    setIsFormOpen(true)
  }

  const handleCloseForm = () => {
    setIsFormOpen(false)
    setEditingItem(null)
  }

  const handleToggleStatus = async (row: Vehicle) => {
    const targetStatus = row.status === 'active' ? 'inactive' : 'active'
    const confirmMsg =
      targetStatus === 'inactive'
        ? `¿Desactivar el vehículo ${row.plate}?`
        : `¿Reactivar el vehículo ${row.plate}?`
    if (!window.confirm(confirmMsg)) return
    setTogglingId(row.id)
    try {
      await vehiclesApi.update(row.id, { status: targetStatus })
      toast.success(
        targetStatus === 'inactive' ? 'Vehículo desactivado' : 'Vehículo reactivado',
      )
      fetchData()
    } catch {
      toast.error('No se pudo cambiar el estado')
    } finally {
      setTogglingId(null)
    }
  }

  const columns: Column<Vehicle>[] = [
    { header: 'Placa', accessor: 'plate' },
    { header: 'Marca', accessor: 'make' },
    { header: 'Modelo', accessor: 'model' },
    { header: 'Año', accessor: (row) => String(row.year) },
    { header: 'Tipo', accessor: 'vehicle_type' },
    {
      header: 'Estado',
      accessor: (row) => (
        <span
          className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
            row.status === 'active'
              ? 'bg-green-100 text-green-700'
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
            disabled={togglingId === row.id}
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
          <h1 className="text-2xl font-bold text-slate-900">Vehículos</h1>
          <p className="text-slate-500 mt-1">Gestión de vehículos asegurados</p>
        </div>
        <Button onClick={handleOpenCreate}>Nuevo Vehículo</Button>
      </div>

      <Input
        placeholder="Buscar por placa, marca o modelo..."
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
        emptyMessage="No se encontraron vehículos."
        getRowKey={(row) => row.id}
      />

      <VehicleFormDialog
        open={isFormOpen}
        onClose={handleCloseForm}
        onSuccess={fetchData}
        initialData={editingItem}
      />
    </div>
  )
}
