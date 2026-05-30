'use client'

import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import { Dialog } from '@/components/ui/dialog'
import {
  vehiclesApi,
  type VehicleCreatePayload,
  type Vehicle,
} from '@/lib/api/vehicles'
import { policiesApi, type Policy } from '@/lib/api/policies'
import { policyholdersApi } from '@/lib/api/policyholders'

interface VehicleFormDialogProps {
  open: boolean
  onClose: () => void
  onSuccess: () => void
  initialData?: Vehicle | null
}

const VEHICLE_TYPE_OPTIONS = [
  { value: 'sedan', label: 'Sedán' },
  { value: 'suv', label: 'SUV' },
  { value: 'pickup', label: 'Pick-up' },
  { value: 'hatchback', label: 'Hatchback' },
  { value: 'van', label: 'Van' },
  { value: 'truck', label: 'Camión' },
  { value: 'motorcycle', label: 'Motocicleta' },
]

export function VehicleFormDialog({
  open,
  onClose,
  onSuccess,
  initialData,
}: VehicleFormDialogProps) {
  const isEdit = !!initialData
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<VehicleCreatePayload>()

  const [policies, setPolicies] = useState<Policy[]>([])
  const [policyholderNames, setPolicyholderNames] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!open) return
    setLoading(true)
    Promise.all([
      policiesApi.list({ limit: 100 }),
      policyholdersApi.list({ limit: 100 }),
    ])
      .then(([polR, phR]) => {
        setPolicies(polR.items)
        const map: Record<string, string> = {}
        for (const ph of phR.items) map[ph.id] = ph.full_name
        setPolicyholderNames(map)
      })
      .catch(() => toast.error('No se pudieron cargar las pólizas'))
      .finally(() => setLoading(false))

    reset({
      plate: initialData?.plate ?? '',
      make: initialData?.make ?? '',
      model: initialData?.model ?? '',
      year: initialData?.year ?? new Date().getFullYear(),
      color: initialData?.color ?? '',
      vehicle_type: initialData?.vehicle_type ?? 'sedan',
      policy_id: initialData?.policy_id ?? '',
    })
  }, [open, initialData, reset])

  const policyOptions = [
    {
      value: '',
      label: loading ? 'Cargando pólizas…' : 'Seleccione una póliza…',
    },
    ...policies.map((p) => ({
      value: p.id,
      label: `${p.policy_number} — ${
        policyholderNames[p.policyholder_id] ?? 'sin asegurado'
      } (vigente hasta ${p.valid_to})`,
    })),
  ]

  const onSubmit = async (data: VehicleCreatePayload) => {
    if (!data.policy_id) {
      toast.error('Seleccione una póliza de la lista')
      return
    }
    try {
      const yearNum = Number(data.year)
      if (isEdit && initialData) {
        await vehiclesApi.update(initialData.id, {
          make: data.make,
          model: data.model,
          year: yearNum,
          color: data.color || null,
          vehicle_type: data.vehicle_type,
          policy_id: data.policy_id,
        })
        toast.success('Vehículo actualizado exitosamente')
      } else {
        await vehiclesApi.create({ ...data, year: yearNum })
        toast.success('Vehículo creado exitosamente')
      }
      reset()
      onSuccess()
      onClose()
    } catch {
      toast.error(isEdit ? 'Error al actualizar el vehículo' : 'Error al crear el vehículo')
    }
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={isEdit ? 'Editar Vehículo' : 'Nuevo Vehículo'}
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="plate">Placa</Label>
          <Input
            id="plate"
            disabled={isEdit}
            {...register('plate', { required: 'La placa es requerida' })}
            placeholder="ABC-123"
          />
          {isEdit && (
            <p className="text-xs text-slate-500">La placa no se puede modificar.</p>
          )}
          {errors.plate && <p className="text-xs text-red-600">{errors.plate.message}</p>}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="make">Marca</Label>
            <Input
              id="make"
              {...register('make', { required: 'La marca es requerida' })}
              placeholder="Toyota"
            />
            {errors.make && <p className="text-xs text-red-600">{errors.make.message}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor="model">Modelo</Label>
            <Input
              id="model"
              {...register('model', { required: 'El modelo es requerido' })}
              placeholder="Corolla"
            />
            {errors.model && <p className="text-xs text-red-600">{errors.model.message}</p>}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="year">Año</Label>
            <Input
              id="year"
              type="number"
              {...register('year', { required: 'El año es requerido', valueAsNumber: true })}
              placeholder="2025"
            />
            {errors.year && <p className="text-xs text-red-600">{errors.year.message}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor="color">Color (opcional)</Label>
            <Input id="color" {...register('color')} placeholder="Blanco" />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="vehicle_type">Tipo de vehículo</Label>
          <Select
            id="vehicle_type"
            options={VEHICLE_TYPE_OPTIONS}
            {...register('vehicle_type', { required: 'El tipo es requerido' })}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="policy_id">Póliza</Label>
          <Select
            id="policy_id"
            options={policyOptions}
            disabled={loading}
            {...register('policy_id', {
              validate: (v) => (v && v !== '') || 'Seleccione una póliza',
            })}
          />
          {errors.policy_id && (
            <p className="text-xs text-red-600">{errors.policy_id.message}</p>
          )}
          {!loading && !isEdit && policies.length === 0 && (
            <p className="text-xs text-amber-600">
              No hay pólizas cargadas. Creá una primero en{' '}
              <span className="font-mono">/dashboard/polizas</span>.
            </p>
          )}
        </div>

        <div className="flex justify-end gap-3 pt-4">
          <Button type="button" variant="outline" onClick={onClose} disabled={isSubmitting}>
            Cancelar
          </Button>
          <Button
            type="submit"
            disabled={isSubmitting || (!isEdit && policies.length === 0)}
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
