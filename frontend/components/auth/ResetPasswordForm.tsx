'use client'

import { useState, Suspense } from 'react'
import { useForm } from 'react-hook-form'
import { useRouter, useSearchParams } from 'next/navigation'
import { Eye, EyeOff, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { isAxiosError } from 'axios'

import { authApi } from '@/lib/api/auth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

interface ResetPasswordFormValues {
  new_password: string
  confirm_password: string
}

function ResetPasswordFormInner() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const token = searchParams.get('token')

  const [showNew, setShowNew] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isValid },
  } = useForm<ResetPasswordFormValues>({
    mode: 'onBlur',
  })

  const newPassword = watch('new_password')

  const onSubmit = async (values: ResetPasswordFormValues) => {
    if (!token) {
      toast.error('Token de restablecimiento no encontrado')
      return
    }

    setIsSubmitting(true)
    try {
      await authApi.confirmPasswordReset(token, values.new_password)
      toast.success('Contraseña actualizada correctamente')
      router.push('/login')
    } catch (error: unknown) {
      if (isAxiosError(error)) {
        const detail = (error.response?.data as { detail?: string })?.detail
        toast.error(detail ?? 'Error al restablecer la contraseña')
      } else {
        toast.error('Error inesperado')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!token) {
    return (
      <div className="text-center space-y-4">
        <p className="text-sm text-red-600">
          Enlace de restablecimiento inválido o expirado.
        </p>
        <a
          href="/login"
          className="inline-block text-sm font-medium text-blue-600 hover:underline"
        >
          Volver al inicio de sesión
        </a>
      </div>
    )
  }

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      noValidate
      aria-label="Formulario de restablecimiento de contraseña"
      className="space-y-5"
    >
      <div className="space-y-1.5">
        <Label htmlFor="new_password">Nueva contraseña</Label>
        <div className="relative">
          <Input
            id="new_password"
            type={showNew ? 'text' : 'password'}
            autoComplete="new-password"
            placeholder="••••••••"
            className="pr-10"
            aria-invalid={!!errors.new_password}
            aria-describedby={
              errors.new_password ? 'new-password-error' : undefined
            }
            {...register('new_password', {
              required: 'La nueva contraseña es requerida',
              minLength: {
                value: 8,
                message: 'Mínimo 8 caracteres',
              },
            })}
          />
          <button
            type="button"
            onClick={() => setShowNew((prev) => !prev)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 cursor-pointer"
            aria-label={showNew ? 'Ocultar contraseña' : 'Mostrar contraseña'}
          >
            {showNew ? (
              <EyeOff className="h-4 w-4" />
            ) : (
              <Eye className="h-4 w-4" />
            )}
          </button>
        </div>
        {errors.new_password && (
          <p
            id="new-password-error"
            role="alert"
            className="text-xs text-red-600"
          >
            {errors.new_password.message}
          </p>
        )}
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="confirm_password">Confirmar contraseña</Label>
        <div className="relative">
          <Input
            id="confirm_password"
            type={showConfirm ? 'text' : 'password'}
            autoComplete="new-password"
            placeholder="••••••••"
            className="pr-10"
            aria-invalid={!!errors.confirm_password}
            aria-describedby={
              errors.confirm_password ? 'confirm-password-error' : undefined
            }
            {...register('confirm_password', {
              required: 'Confirmá tu nueva contraseña',
              validate: (value) =>
                value === newPassword || 'Las contraseñas no coinciden',
            })}
          />
          <button
            type="button"
            onClick={() => setShowConfirm((prev) => !prev)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 cursor-pointer"
            aria-label={
              showConfirm ? 'Ocultar contraseña' : 'Mostrar contraseña'
            }
          >
            {showConfirm ? (
              <EyeOff className="h-4 w-4" />
            ) : (
              <Eye className="h-4 w-4" />
            )}
          </button>
        </div>
        {errors.confirm_password && (
          <p
            id="confirm-password-error"
            role="alert"
            className="text-xs text-red-600"
          >
            {errors.confirm_password.message}
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
        {isSubmitting ? 'Guardando...' : 'Guardar nueva contraseña'}
      </Button>
    </form>
  )
}

export function ResetPasswordForm() {
  return (
    <Suspense
      fallback={
        <div className="flex justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
        </div>
      }
    >
      <ResetPasswordFormInner />
    </Suspense>
  )
}
