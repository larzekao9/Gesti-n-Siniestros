import { z } from 'zod'

export const loginSchema = z.object({
  tenant_slug: z
    .string()
    .min(1, 'El identificador de organización es requerido')
    .regex(/^[a-z0-9-]+$/, 'Solo letras minúsculas, números y guiones'),
  email: z.string().email('Email inválido'),
  password: z.string().min(1, 'La contraseña es requerida'),
  mfa_code: z
    .string()
    .length(6, 'El código debe tener 6 dígitos')
    .optional()
    .or(z.literal('')),
})

export const registerSchema = z.object({
  full_name: z
    .string()
    .min(2, 'El nombre debe tener al menos 2 caracteres')
    .max(100, 'El nombre no puede superar los 100 caracteres'),
  email: z.string().email('Email inválido'),
  password: z
    .string()
    .min(8, 'La contraseña debe tener al menos 8 caracteres')
    .regex(/[A-Z]/, 'Debe contener al menos una mayúscula')
    .regex(/[0-9]/, 'Debe contener al menos un número'),
  tenant_slug: z
    .string()
    .min(1, 'El identificador de organización es requerido')
    .regex(
      /^[a-z0-9-]+$/,
      'Solo letras minúsculas, números y guiones'
    ),
})

export const mfaVerifySchema = z.object({
  code: z
    .string()
    .length(6, 'El código debe tener exactamente 6 dígitos')
    .regex(/^\d+$/, 'Solo se permiten dígitos'),
})

export type LoginFormValues = z.infer<typeof loginSchema>
export type RegisterFormValues = z.infer<typeof registerSchema>
export type MFAVerifyFormValues = z.infer<typeof mfaVerifySchema>
