'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useRouter } from 'next/navigation'
import { Loader2, ShieldCheck } from 'lucide-react'
import { toast } from 'sonner'
import { isAxiosError } from 'axios'

import { mfaVerifySchema, type MFAVerifyFormValues } from '@/lib/validations/auth'
import { authApi } from '@/lib/api/auth'
import { useAuthStore } from '@/lib/stores/authStore'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export function MFAVerifyForm() {
  const router = useRouter()
  const { user, setAuth, accessToken, tenantSlug } = useAuthStore()
  const [isSubmitting, setIsSubmitting] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
    reset,
  } = useForm<MFAVerifyFormValues>({
    resolver: zodResolver(mfaVerifySchema),
    mode: 'onChange',
  })

  const onSubmit = async (values: MFAVerifyFormValues) => {
    setIsSubmitting(true)
    try {
      await authApi.verifyMFA(values.code)
      // Refrescar el usuario desde el servidor para reflejar el estado real
      // (mfa_enabled = true). Si /me fallara, caemos al update optimista para
      // no dejar el badge desactualizado — el verify ya activó MFA en el server.
      if (accessToken) {
        const refreshToken = localStorage.getItem('siniestros_rt') ?? ''
        try {
          const freshUser = await authApi.getMe()
          setAuth(freshUser, accessToken, refreshToken, tenantSlug ?? '')
        } catch {
          if (user) {
            setAuth(
              { ...user, mfa_enabled: true },
              accessToken,
              refreshToken,
              tenantSlug ?? ''
            )
          }
        }
      }
      toast.success('Autenticación en dos pasos activada correctamente')
      router.push('/dashboard')
    } catch (error: unknown) {
      if (isAxiosError(error)) {
        const detail = (error.response?.data as { detail?: string })?.detail
        toast.error(detail ?? 'Código inválido o expirado.')
      } else {
        toast.error('Error inesperado. Intentá nuevamente.')
      }
      console.error('[MFAVerifyForm] error:', error)
      reset()
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      noValidate
      aria-label="Formulario de verificación MFA"
      className="space-y-5"
    >
      <div className="flex flex-col items-center gap-2 pb-2">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-100">
          <ShieldCheck className="h-6 w-6 text-blue-600" aria-hidden="true" />
        </div>
        <p className="text-sm text-slate-600 text-center">
          Ingresá el código de 6 dígitos que muestra tu aplicación de autenticación.
        </p>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="code">Código de verificación</Label>
        <Input
          id="code"
          type="text"
          inputMode="numeric"
          autoComplete="one-time-code"
          placeholder="000000"
          maxLength={6}
          aria-invalid={!!errors.code}
          aria-describedby={errors.code ? 'code-error' : 'code-hint'}
          className="text-center text-2xl tracking-widest font-mono"
          {...register('code')}
        />
        {errors.code ? (
          <p id="code-error" role="alert" className="text-xs text-red-600">
            {errors.code.message}
          </p>
        ) : (
          <p id="code-hint" className="text-xs text-slate-500 text-center">
            El código se renueva cada 30 segundos.
          </p>
        )}
      </div>

      <Button
        type="submit"
        className="w-full"
        disabled={isSubmitting || !isValid}
        aria-busy={isSubmitting}
      >
        {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />}
        {isSubmitting ? 'Verificando...' : 'Verificar código'}
      </Button>
    </form>
  )
}
