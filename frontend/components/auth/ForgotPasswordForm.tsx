'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import Link from 'next/link'
import { Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { isAxiosError } from 'axios'

import { authApi } from '@/lib/api/auth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

interface ForgotPasswordFormValues {
  email: string
  tenant_slug: string
}

export function ForgotPasswordForm() {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
  } = useForm<ForgotPasswordFormValues>({
    mode: 'onBlur',
  })

  const onSubmit = async (values: ForgotPasswordFormValues) => {
    setIsSubmitting(true)
    try {
      await authApi.requestPasswordReset(values.email, values.tenant_slug)
      setSubmitted(true)
      toast.success('Si el email existe, recibirás un enlace')
    } catch (error: unknown) {
      if (isAxiosError(error)) {
        const detail = (error.response?.data as { detail?: string })?.detail
        toast.error(detail ?? 'Error al solicitar el restablecimiento')
      } else {
        toast.error('Error inesperado. Intentá nuevamente.')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  if (submitted) {
    return (
      <div className="text-center space-y-4">
        <p className="text-sm text-slate-600">
          Si el email ingresado corresponde a una cuenta activa, recibirás un
          enlace para restablecer tu contraseña.
        </p>
        <Link
          href="/login"
          className="inline-block text-sm font-medium text-blue-600 hover:underline"
        >
          Volver al inicio de sesión
        </Link>
      </div>
    )
  }

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      noValidate
      aria-label="Formulario de recuperación de contraseña"
      className="space-y-5"
    >
      <div className="space-y-1.5">
        <Label htmlFor="email">Correo electrónico</Label>
        <Input
          id="email"
          type="email"
          autoComplete="email"
          placeholder="correo@ejemplo.com"
          aria-invalid={!!errors.email}
          aria-describedby={errors.email ? 'email-error' : undefined}
          {...register('email', {
            required: 'El correo electrónico es requerido',
          })}
        />
        {errors.email && (
          <p id="email-error" role="alert" className="text-xs text-red-600">
            {errors.email.message}
          </p>
        )}
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="tenant_slug">Organización</Label>
        <Input
          id="tenant_slug"
          type="text"
          autoComplete="organization"
          placeholder="nombre-de-tu-aseguradora"
          aria-invalid={!!errors.tenant_slug}
          aria-describedby={
            errors.tenant_slug ? 'tenant-error' : undefined
          }
          {...register('tenant_slug', {
            required: 'La organización es requerida',
          })}
        />
        {errors.tenant_slug && (
          <p id="tenant-error" role="alert" className="text-xs text-red-600">
            {errors.tenant_slug.message}
          </p>
        )}
      </div>

      <Button
        type="submit"
        className="w-full"
        disabled={isSubmitting || !isValid}
        aria-busy={isSubmitting}
      >
        {isSubmitting && (
          <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
        )}
        {isSubmitting ? 'Enviando...' : 'Enviar enlace'}
      </Button>

      <p className="text-center text-sm text-slate-600">
        <Link
          href="/login"
          className="font-medium text-blue-600 hover:underline focus-visible:underline focus-visible:outline-none"
        >
          Volver al inicio de sesión
        </Link>
      </p>
    </form>
  )
}
