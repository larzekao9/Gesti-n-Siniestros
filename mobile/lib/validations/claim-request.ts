// Validaciones del wizard de reporte (CU-03 datos del accidente).
import { z } from 'zod'

export const vehicleStepSchema = z.object({
  policy_id: z.string().min(1, 'Seleccioná una póliza'),
  vehicle_id: z.string().min(1, 'Seleccioná el vehículo del siniestro'),
})

export const accidentStepSchema = z.object({
  accident_date: z
    .string()
    .min(1, 'La fecha del accidente es requerida')
    .regex(/^\d{4}-\d{2}-\d{2}$/, 'Formato de fecha inválido (AAAA-MM-DD)'),
  accident_time: z.string().optional().or(z.literal('')),
  accident_location: z
    .string()
    .min(3, 'Describí el lugar del accidente')
    .max(500, 'Máximo 500 caracteres'),
  accident_lat: z.number().nullable().optional(),
  accident_lng: z.number().nullable().optional(),
  accident_description: z
    .string()
    .min(10, 'Contanos qué pasó (mínimo 10 caracteres)')
    .max(2000, 'Máximo 2000 caracteres'),
  reported_damages: z.string().max(2000, 'Máximo 2000 caracteres').optional().or(z.literal('')),
})

export type VehicleStepValues = z.infer<typeof vehicleStepSchema>
export type AccidentStepValues = z.infer<typeof accidentStepSchema>
