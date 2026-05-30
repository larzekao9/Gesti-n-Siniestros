'use client'

import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { Dialog } from '@/components/ui/dialog'
import {
  policiesApi,
  type PolicyCreatePayload,
  type Policy,
} from '@/lib/api/policies'
import { policyholdersApi, type Policyholder } from '@/lib/api/policyholders'

interface PolicyFormDialogProps {
  open: boolean
  onClose: () => void
  onSuccess: () => void
  initialData?: Policy | null
}

export function PolicyFormDialog({
  open,
  onClose,
  onSuccess,
  initialData,
}: PolicyFormDialogProps) {
  const isEdit = !!initialData
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<PolicyCreatePayload>()

  const [policyholders, setPolicyholders] = useState<Policyholder[]>([])
  const [loadingPolicyholders, setLoadingPolicyholders] = useState(false)

  useEffect(() => {
    if (!open) return
    setLoadingPolicyholders(true)
    policyholdersApi
      .list({ limit: 100 })
      .then((r) => setPolicyholders(r.items))
      .catch(() => toast.error('No se pudieron cargar los asegurados'))
      .finally(() => setLoadingPolicyholders(false))

    reset({
      policy_number: initialData?.policy_number ?? '',
      policyholder_id: initialData?.policyholder_id ?? '',
      valid_from: initialData?.valid_from ?? '',
      valid_to: initialData?.valid_to ?? '',
      coverage_type: initialData?.coverage_type ?? '',
      exclusions: initialData?.exclusions ?? '',
    })
  }, [open, initialData, reset])

  const policyholderOptions = [
    {
      value: '',
      label: loadingPolicyholders ? 'Cargando asegurados…' : 'Seleccione un asegurado…',
    },
    ...policyholders.map((p) => ({
      value: p.id,
      label: `${p.full_name} — ${p.document_id}`,
    })),
  ]

  const onSubmit = async (data: PolicyCreatePayload) => {
    if (!isEdit && !data.policyholder_id) {
      toast.error('Seleccione un asegurado de la lista')
      return
    }
    try {
      if (isEdit && initialData) {
        await policiesApi.update(initialData.id, {
          policy_number: data.policy_number,
          valid_from: data.valid_from,
          valid_to: data.valid_to,
          coverage_type: data.coverage_type,
          exclusions: data.exclusions || null,
        })
        toast.success('Póliza actualizada exitosamente')
      } else {
        await policiesApi.create(data)
        toast.success('Póliza creada exitosamente')
      }
      reset()
      onSuccess()
      onClose()
    } catch {
      toast.error(isEdit ? 'Error al actualizar la póliza' : 'Error al crear la póliza')
    }
  }

  return (
    <Dialog open={open} onClose={onClose} title={isEdit ? 'Editar Póliza' : 'Nueva Póliza'}>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="policy_number">Número de póliza</Label>
          <Input
            id="policy_number"
            {...register('policy_number', { required: 'El número de póliza es requerido' })}
            placeholder="POL-2026-001"
          />
          {errors.policy_number && (
            <p className="text-xs text-red-600">{errors.policy_number.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="policyholder_id">Asegurado</Label>
          <Select
            id="policyholder_id"
            options={policyholderOptions}
            disabled={loadingPolicyholders || isEdit}
            {...register('policyholder_id', {
              validate: (v) => isEdit || (v && v !== '') || 'Seleccione un asegurado',
            })}
          />
          {isEdit && (
            <p className="text-xs text-slate-500">
              El asegurado titular no se puede cambiar después de creada la póliza.
            </p>
          )}
          {errors.policyholder_id && (
            <p className="text-xs text-red-600">{errors.policyholder_id.message}</p>
          )}
          {!loadingPolicyholders && !isEdit && policyholders.length === 0 && (
            <p className="text-xs text-amber-600">
              No hay asegurados cargados. Creá uno primero en{' '}
              <span className="font-mono">/dashboard/asegurados</span>.
            </p>
          )}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="valid_from">Vigencia desde</Label>
            <Input
              id="valid_from"
              type="date"
              {...register('valid_from', { required: 'La fecha de inicio es requerida' })}
            />
            {errors.valid_from && (
              <p className="text-xs text-red-600">{errors.valid_from.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="valid_to">Vigencia hasta</Label>
            <Input
              id="valid_to"
              type="date"
              {...register('valid_to', { required: 'La fecha de fin es requerida' })}
            />
            {errors.valid_to && (
              <p className="text-xs text-red-600">{errors.valid_to.message}</p>
            )}
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="coverage_type">Tipo de cobertura</Label>
          <Input
            id="coverage_type"
            {...register('coverage_type', { required: 'El tipo de cobertura es requerido' })}
            placeholder="Todo Riesgo / Terceros / etc."
          />
          {errors.coverage_type && (
            <p className="text-xs text-red-600">{errors.coverage_type.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="exclusions">Exclusiones (opcional)</Label>
          <Textarea
            id="exclusions"
            {...register('exclusions')}
            placeholder="Detalle de exclusiones de la póliza"
            rows={3}
          />
        </div>

        <div className="flex justify-end gap-3 pt-4">
          <Button type="button" variant="outline" onClick={onClose} disabled={isSubmitting}>
            Cancelar
          </Button>
          <Button
            type="submit"
            disabled={isSubmitting || (!isEdit && policyholders.length === 0)}
          >
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
