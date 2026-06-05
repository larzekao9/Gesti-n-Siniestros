// ★ Validaciones del canal asegurado. Reutiliza el patrón Zod de
// /frontend/lib/validations/auth.ts adaptado al login del asegurado.
import { z } from 'zod'

const tenantSlug = z
  .string()
  .min(1, 'El identificador de tu aseguradora es requerido')
  .regex(/^[a-z0-9-]+$/, 'Solo minúsculas, números y guiones')

const strongPassword = z
  .string()
  .min(8, 'La contraseña debe tener al menos 8 caracteres')
  .regex(/[A-Z]/, 'Debe contener al menos una mayúscula')
  .regex(/[0-9]/, 'Debe contener al menos un número')

export const insuredLoginSchema = z.object({
  tenant_slug: tenantSlug,
  email: z.string().email('Email inválido'),
  password: z.string().min(1, 'La contraseña es requerida'),
})

export const registerWithTokenSchema = z
  .object({
    activation_token: z.string().min(10, 'Token de activación inválido'),
    password: strongPassword,
    confirm_password: z.string(),
  })
  .refine((d) => d.password === d.confirm_password, {
    message: 'Las contraseñas no coinciden',
    path: ['confirm_password'],
  })

export const forgotPasswordSchema = z.object({
  tenant_slug: tenantSlug,
  email: z.string().email('Email inválido'),
})

export type InsuredLoginValues = z.infer<typeof insuredLoginSchema>
export type RegisterWithTokenValues = z.infer<typeof registerWithTokenSchema>
export type ForgotPasswordValues = z.infer<typeof forgotPasswordSchema>
