'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { toast } from 'sonner'
import { useAuthStore } from '@/lib/stores/authStore'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { DataTable, type Column } from '@/components/ui/data-table'
import { UserFormDialog } from '@/components/users/UserFormDialog'
import { usersApi } from '@/lib/api/users'
import type { User } from '@/types/auth'

interface UserListItem extends User {
  is_active?: boolean
}

const LIMIT = 20

export default function UsuariosPage() {
  const currentUser = useAuthStore((s) => s.user)
  const isAdmin = currentUser?.role === 'admin'

  const [data, setData] = useState<UserListItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<User | null>(null)
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
      const result = await usersApi.list({
        page,
        limit: LIMIT,
        search: debouncedSearch || undefined,
      })
      setData(result.items as UserListItem[])
      setTotal(result.total)
    } catch {
      toast.error('Error al cargar los usuarios')
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

  const handleOpenEdit = (row: User) => {
    setEditingItem(row)
    setIsFormOpen(true)
  }

  const handleCloseForm = () => {
    setIsFormOpen(false)
    setEditingItem(null)
  }

  const handleToggleStatus = async (row: UserListItem) => {
    const wasActive = row.is_active !== false
    const targetActive = !wasActive
    const confirmMsg = wasActive
      ? `¿Desactivar al usuario "${row.email}"? No podrá iniciar sesión hasta ser reactivado.`
      : `¿Reactivar al usuario "${row.email}"?`
    if (!window.confirm(confirmMsg)) return
    setTogglingId(row.id)
    try {
      await usersApi.update(row.id, { is_active: targetActive })
      toast.success(wasActive ? 'Usuario desactivado' : 'Usuario reactivado')
      fetchData()
    } catch {
      toast.error('No se pudo cambiar el estado')
    } finally {
      setTogglingId(null)
    }
  }

  const columns: Column<UserListItem>[] = [
    { header: 'Email', accessor: 'email' },
    { header: 'Nombre', accessor: 'full_name' },
    {
      header: 'Rol',
      accessor: (row) => (
        <span className="inline-flex rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700 capitalize">
          {row.role === 'admin'
            ? 'Administrador'
            : row.role === 'supervisor'
              ? 'Supervisor'
              : 'Analista'}
        </span>
      ),
    },
    {
      header: 'Estado',
      accessor: (row) => {
        const active = row.is_active !== false
        return (
          <span
            className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
              active ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-500'
            }`}
          >
            {active ? 'Activo' : 'Inactivo'}
          </span>
        )
      },
    },
    {
      header: 'MFA',
      accessor: (row) => (
        <span
          className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
            row.mfa_enabled
              ? 'bg-green-100 text-green-700'
              : 'bg-slate-100 text-slate-500'
          }`}
        >
          {row.mfa_enabled ? 'Activado' : 'Inactivo'}
        </span>
      ),
    },
    {
      header: 'Acciones',
      accessor: (row) => {
        if (!isAdmin) return <span className="text-xs text-slate-400">—</span>
        const isSelf = row.id === currentUser?.id
        const active = row.is_active !== false
        return (
          <div className="flex gap-1">
            <Button variant="ghost" size="sm" onClick={() => handleOpenEdit(row)}>
              Editar
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className={
                active
                  ? 'text-red-600 hover:text-red-700 hover:bg-red-50'
                  : 'text-green-600 hover:text-green-700 hover:bg-green-50'
              }
              onClick={() => handleToggleStatus(row)}
              disabled={togglingId === row.id || isSelf}
              title={isSelf ? 'No podés desactivarte a vos mismo.' : undefined}
            >
              {togglingId === row.id ? '…' : active ? 'Desactivar' : 'Reactivar'}
            </Button>
          </div>
        )
      },
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Usuarios</h1>
          <p className="text-slate-500 mt-1">Gestión de usuarios del sistema</p>
        </div>
        {isAdmin && <Button onClick={handleOpenCreate}>Nuevo Usuario</Button>}
      </div>

      <Input
        placeholder="Buscar por email o nombre..."
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
        emptyMessage="No se encontraron usuarios."
        getRowKey={(row) => row.id}
      />

      {isAdmin && (
        <UserFormDialog
          open={isFormOpen}
          onClose={handleCloseForm}
          onSuccess={fetchData}
          initialData={editingItem}
        />
      )}
    </div>
  )
}
