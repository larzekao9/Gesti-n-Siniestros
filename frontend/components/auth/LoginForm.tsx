'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Eye, EyeOff, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { isAxiosError } from 'axios'

import { loginSchema, type LoginFormValues } from '@/lib/validations/auth'
import { authApi } from '@/lib/api/auth'
import { useAuthStore } from '@/lib/stores/authStore'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export function LoginForm() {
  const router = useRouter()
  const { setAuth } = useAuthStore()
  const [showPassword, setShowPassword] = useState(false)
  const [needsMFA, setNeedsMFA] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    mode: 'onBlur',
  })

  const onSubmit = async (values: LoginFormValues) => {
    setIsSubmitting(true)
    try {
      const response = await authApi.login({
        email: values.email,
        password: values.password,
        tenant_slug: values.tenant_slug,
        mfa_code: values.mfa_code || undefined,
      })
      setAuth(response.user, response.access_token, response.refresh_token, values.tenant_slug)
      toast.success('Sesión iniciada correctamente')
      router.push('/dashboard')
    } catch (error: unknown) {
      if (isAxiosError(error)) {
        const status = error.response?.status
        const detail = (error.response?.data as { detail?: string })?.detail

        if (status === 403 && detail?.toLowerCase().includes('mfa')) {
          setNeedsMFA(true)
          toast.info('Ingresá tu código de autenticación')
          return
        }

        if (status === 401) {
          toast.error('Email o contraseña incorrectos')
        } else {
          toast.error(detail ?? 'Error al iniciar sesión. Intentá nuevamente.')
        }
      } else {
        toast.error('Error inesperado. Intentá nuevamente.')
      }
      console.error('[LoginForm] error:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      noValidate
      aria-label="Formulario de inicio de sesión"
      className="space-y-5"
    >
      {/* Organización */}
      <div className="space-y-1.5">
        <Label htmlFor="tenant_slug">Organización</Label>
        <Input
          id="tenant_slug"
          type="text"
          autoComplete="organization"
          placeholder="nombre-de-tu-aseguradora"
          aria-invalid={!!errors.tenant_slug}
          aria-describedby={errors.tenant_slug ? 'tenant-error' : undefined}
          {...register('tenant_slug')}
        />
        {errors.tenant_slug && (
          <p id="tenant-error" role="alert" className="text-xs text-red-600">
            {errors.tenant_slug.message}
          </p>
        )}
      </div>

      {/* Email */}
      <div className="space-y-1.5">
        <Label htmlFor="email">Correo electrónico</Label>
        <Input
          id="email"
          type="email"
          autoComplete="email"
          placeholder="correo@ejemplo.com"
          aria-invalid={!!errors.email}
          aria-describedby={errors.email ? 'email-error' : undefined}
          {...register('email')}
        />
        {errors.email && (
          <p id="email-error" role="alert" className="text-xs text-red-600">
            {errors.email.message}
          </p>
        )}
      </div>

      {/* Password */}
      <div className="space-y-1.5">
        <Label htmlFor="password">Contraseña</Label>
        <div className="relative">
          <Input
            id="password"
            type={showPassword ? 'text' : 'password'}
            autoComplete="current-password"
            placeholder="••••••••"
            aria-invalid={!!errors.password}
            aria-describedby={errors.password ? 'password-error' : undefined}
            className="pr-10"
            {...register('password')}
          />
          <button
            type="button"
            onClick={() => setShowPassword((prev) => !prev)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 cursor-pointer"
            aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
          >
            {showPassword ? (
              <EyeOff className="h-4 w-4" />
            ) : (
              <Eye className="h-4 w-4" />
            )}
          </button>
        </div>
        {errors.password && (
          <p id="password-error" role="alert" className="text-xs text-red-600">
            {errors.password.message}
          </p>
        )}
      </div>

      {/* MFA Code — shown conditionally */}
      {needsMFA && (
        <div className="space-y-1.5">
          <Label htmlFor="mfa_code">Código de autenticación (6 dígitos)</Label>
          <Input
            id="mfa_code"
            type="text"
            inputMode="numeric"
            autoComplete="one-time-code"
            placeholder="000000"
            maxLength={6}
            aria-invalid={!!errors.mfa_code}
            aria-describedby={errors.mfa_code ? 'mfa-error' : undefined}
            {...register('mfa_code')}
          />
          {errors.mfa_code && (
            <p id="mfa-error" role="alert" className="text-xs text-red-600">
              {errors.mfa_code.message}
            </p>
          )}
          <p className="text-xs text-slate-500">
            Ingresá el código de tu aplicación de autenticación (Google Authenticator o Authy).
          </p>
        </div>
      )}

      {/* Submit */}
      <Button
        type="submit"
        className="w-full"
        disabled={isSubmitting || (!isValid && !needsMFA)}
        aria-busy={isSubmitting}
      >
        {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />}
        {isSubmitting ? 'Ingresando...' : 'Iniciar sesión'}
      </Button>

      <p className="text-center text-sm text-slate-600">
        ¿No tenés una cuenta?{' '}
        <Link
          href="/register"
          className="font-medium text-blue-600 hover:underline focus-visible:underline focus-visible:outline-none"
        >
          Registrarse
        </Link>
      </p>
    </form>
  )
}
