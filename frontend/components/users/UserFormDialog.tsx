'use client'

import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import { Dialog } from '@/components/ui/dialog'
import { usersApi, type UserCreatePayload } from '@/lib/api/users'
import type { User } from '@/types/auth'

interface UserFormDialogProps {
  open: boolean
  onClose: () => void
  onSuccess: () => void
  initialData?: User | null
}

const ROLE_OPTIONS = [
  { value: 'analyst', label: 'Analista' },
  { value: 'supervisor', label: 'Supervisor' },
  { value: 'admin', label: 'Administrador' },
]

export function UserFormDialog({
  open,
  onClose,
  onSuccess,
  initialData,
}: UserFormDialogProps) {
  const isEdit = !!initialData
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<UserCreatePayload>({
    defaultValues: { role: 'analyst' },
  })

  useEffect(() => {
    if (open) {
      reset({
        email: initialData?.email ?? '',
        full_name: initialData?.full_name ?? '',
        role: initialData?.role ?? 'analyst',
        password: '',
      })
    }
  }, [open, initialData, reset])

  const onSubmit = async (data: UserCreatePayload) => {
    try {
      if (isEdit && initialData) {
        // En edit: solo enviar campos modificables. Password solo si se ingresó.
        const payload: { full_name: string; role: string; password?: string } = {
          full_name: data.full_name,
          role: data.role,
        }
        if (data.password && data.password.length > 0) {
          payload.password = data.password
        }
        await usersApi.update(initialData.id, payload)
        toast.success('Usuario actualizado exitosamente')
      } else {
        await usersApi.create(data)
        toast.success('Usuario creado exitosamente')
      }
      reset()
      onSuccess()
      onClose()
    } catch {
      toast.error(isEdit ? 'Error al actualizar el usuario' : 'Error al crear el usuario')
    }
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={isEdit ? 'Editar Usuario' : 'Nuevo Usuario'}
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            disabled={isEdit}
            {...register('email', { required: 'El email es requerido' })}
            placeholder="usuario@example.com"
          />
          {isEdit && (
            <p className="text-xs text-slate-500">El email no se puede modificar.</p>
          )}
          {errors.email && (
            <p className="text-xs text-red-600">{errors.email.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="password">
            {isEdit ? 'Nueva contraseña (opcional)' : 'Contraseña'}
          </Label>
          <Input
            id="password"
            type="password"
            {...register('password', {
              required: isEdit ? false : 'La contraseña es requerida',
            })}
            placeholder={isEdit ? 'Dejar vacío para no cambiar' : '••••••••'}
          />
          {errors.password && (
            <p className="text-xs text-red-600">{errors.password.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="full_name">Nombre completo</Label>
          <Input
            id="full_name"
            {...register('full_name', { required: 'El nombre es requerido' })}
            placeholder="María López"
          />
          {errors.full_name && (
            <p className="text-xs text-red-600">{errors.full_name.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="role">Rol</Label>
          <Select
            id="role"
            options={ROLE_OPTIONS}
            {...register('role', { required: 'El rol es requerido' })}
          />
          {errors.role && (
            <p className="text-xs text-red-600">{errors.role.message}</p>
          )}
        </div>

        <div className="flex justify-end gap-3 pt-4">
          <Button type="button" variant="outline" onClick={onClose} disabled={isSubmitting}>
            Cancelar
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting
              ? 'Guardando…'
              : isEdit
                ? 'Guardar cambios'
                : 'Crear'}
          </Button>
        </div>
      </form>
    </Dialog>
  )
}
