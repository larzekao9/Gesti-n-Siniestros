'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Eye, EyeOff, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { isAxiosError } from 'axios'

import { authApi } from '@/lib/api/auth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Dialog } from '@/components/ui/dialog'

interface ChangePasswordFormValues {
  current_password: string
  new_password: string
  confirm_password: string
}

interface ChangePasswordDialogProps {
  open: boolean
  onClose: () => void
}

export function ChangePasswordDialog({
  open,
  onClose,
}: ChangePasswordDialogProps) {
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isValid },
    reset,
  } = useForm<ChangePasswordFormValues>({
    mode: 'onBlur',
  })

  const [showCurrent, setShowCurrent] = useState(false)
  const [showNew, setShowNew] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const newPassword = watch('new_password')

  const onSubmit = async (values: ChangePasswordFormValues) => {
    setIsSubmitting(true)
    try {
      await authApi.changePassword(
        values.current_password,
        values.new_password,
        values.confirm_password
      )
      toast.success('Contraseña actualizada correctamente')
      reset()
      onClose()
    } catch (error: unknown) {
      if (isAxiosError(error)) {
        const detail = (error.response?.data as { detail?: string })?.detail
        toast.error(detail ?? 'Error al cambiar la contraseña')
      } else {
        toast.error('Error inesperado')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleClose = () => {
    reset()
    onClose()
  }

  return (
    <Dialog open={open} onClose={handleClose} title="Cambiar contraseña">
      <form
        onSubmit={handleSubmit(onSubmit)}
        noValidate
        aria-label="Formulario de cambio de contraseña"
        className="space-y-4"
      >
        {/* Current password */}
        <div className="space-y-1.5">
          <Label htmlFor="current_password">Contraseña actual</Label>
          <div className="relative">
            <Input
              id="current_password"
              type={showCurrent ? 'text' : 'password'}
              autoComplete="current-password"
              placeholder="••••••••"
              className="pr-10"
              {...register('current_password', {
                required: 'La contraseña actual es requerida',
              })}
            />
            <button
              type="button"
              onClick={() => setShowCurrent((prev) => !prev)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 cursor-pointer"
              aria-label={showCurrent ? 'Ocultar contraseña' : 'Mostrar contraseña'}
            >
              {showCurrent ? (
                <EyeOff className="h-4 w-4" />
              ) : (
                <Eye className="h-4 w-4" />
              )}
            </button>
          </div>
          {errors.current_password && (
            <p role="alert" className="text-xs text-red-600">
              {errors.current_password.message}
            </p>
          )}
        </div>

        {/* New password */}
        <div className="space-y-1.5">
          <Label htmlFor="new_password">Nueva contraseña</Label>
          <div className="relative">
            <Input
              id="new_password"
              type={showNew ? 'text' : 'password'}
              autoComplete="new-password"
              placeholder="••••••••"
              className="pr-10"
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
            <p role="alert" className="text-xs text-red-600">
              {errors.new_password.message}
            </p>
          )}
        </div>

        {/* Confirm password */}
        <div className="space-y-1.5">
          <Label htmlFor="confirm_password">Confirmar contraseña</Label>
          <div className="relative">
            <Input
              id="confirm_password"
              type={showConfirm ? 'text' : 'password'}
              autoComplete="new-password"
              placeholder="••••••••"
              className="pr-10"
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
            <p role="alert" className="text-xs text-red-600">
              {errors.confirm_password.message}
            </p>
          )}
        </div>

        <div className="flex gap-3 pt-2">
          <Button
            type="button"
            variant="outline"
            className="flex-1"
            onClick={handleClose}
            disabled={isSubmitting}
          >
            Cancelar
          </Button>
          <Button
            type="submit"
            className="flex-1"
            disabled={isSubmitting || !isValid}
            aria-busy={isSubmitting}
          >
            {isSubmitting && (
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            )}
            {isSubmitting ? 'Guardando...' : 'Guardar'}
          </Button>
        </div>
      </form>
    </Dialog>
  )
}
