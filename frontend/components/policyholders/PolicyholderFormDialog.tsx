'use client'

import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Dialog } from '@/components/ui/dialog'
import {
  policyholdersApi,
  type PolicyholderCreatePayload,
  type Policyholder,
} from '@/lib/api/policyholders'

interface PolicyholderFormDialogProps {
  open: boolean
  onClose: () => void
  onSuccess: () => void
  initialData?: Policyholder | null
}

export function PolicyholderFormDialog({
  open,
  onClose,
  onSuccess,
  initialData,
}: PolicyholderFormDialogProps) {
  const isEdit = !!initialData
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<PolicyholderCreatePayload>()

  useEffect(() => {
    if (open) {
      reset({
        document_id: initialData?.document_id ?? '',
        full_name: initialData?.full_name ?? '',
        phone: initialData?.phone ?? '',
        email: initialData?.email ?? '',
        address: initialData?.address ?? '',
      })
    }
  }, [open, initialData, reset])

  const onSubmit = async (data: PolicyholderCreatePayload) => {
    try {
      if (isEdit && initialData) {
        await policyholdersApi.update(initialData.id, {
          full_name: data.full_name,
          phone: data.phone,
          email: data.email || null,
          address: data.address || null,
        })
        toast.success('Asegurado actualizado exitosamente')
      } else {
        await policyholdersApi.create(data)
        toast.success('Asegurado creado exitosamente')
      }
      reset()
      onSuccess()
      onClose()
    } catch {
      toast.error(isEdit ? 'Error al actualizar el asegurado' : 'Error al crear el asegurado')
    }
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={isEdit ? 'Editar Asegurado' : 'Nuevo Asegurado'}
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="document_id">Documento (CI/NIT)</Label>
          <Input
            id="document_id"
            disabled={isEdit}
            {...register('document_id', { required: 'El documento es requerido' })}
            placeholder="12345678"
          />
          {isEdit && (
            <p className="text-xs text-slate-500">
              El documento no se puede modificar.
            </p>
          )}
          {errors.document_id && (
            <p className="text-xs text-red-600">{errors.document_id.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="full_name">Nombre completo</Label>
          <Input
            id="full_name"
            {...register('full_name', { required: 'El nombre es requerido' })}
            placeholder="Juan Pérez"
          />
          {errors.full_name && (
            <p className="text-xs text-red-600">{errors.full_name.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="phone">Teléfono</Label>
          <Input
            id="phone"
            {...register('phone', { required: 'El teléfono es requerido' })}
            placeholder="+591 77777777"
          />
          {errors.phone && (
            <p className="text-xs text-red-600">{errors.phone.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="email">Email (opcional)</Label>
          <Input
            id="email"
            type="email"
            {...register('email')}
            placeholder="juan@example.com"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="address">Dirección (opcional)</Label>
          <Input
            id="address"
            {...register('address')}
            placeholder="Av. Principal #123"
          />
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
