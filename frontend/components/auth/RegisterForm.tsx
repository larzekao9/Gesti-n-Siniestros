'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Eye, EyeOff, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { isAxiosError } from 'axios'

import { registerSchema, type RegisterFormValues } from '@/lib/validations/auth'
import { authApi } from '@/lib/api/auth'
import { useAuthStore } from '@/lib/stores/authStore'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export function RegisterForm() {
  const router = useRouter()
  const { setAuth } = useAuthStore()
  const [showPassword, setShowPassword] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    mode: 'onBlur',
  })

  const onSubmit = async (values: RegisterFormValues) => {
    setIsSubmitting(true)
    try {
      const response = await authApi.register(values)
      setAuth(response.user, response.access_token, response.refresh_token, values.tenant_slug)
      toast.success('Cuenta creada correctamente. Configurá tu autenticación en dos pasos.')
      router.push('/mfa/setup')
    } catch (error: unknown) {
      if (isAxiosError(error)) {
        const status = error.response?.status
        const detail = (error.response?.data as { detail?: string })?.detail

        if (status === 409) {
          toast.error('Ya existe una cuenta con ese correo electrónico.')
        } else {
          toast.error(detail ?? 'Error al crear la cuenta. Intentá nuevamente.')
        }
      } else {
        toast.error('Error inesperado. Intentá nuevamente.')
      }
      console.error('[RegisterForm] error:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      noValidate
      aria-label="Formulario de registro"
      className="space-y-5"
    >
      {/* Full name */}
      <div className="space-y-1.5">
        <Label htmlFor="full_name">Nombre completo</Label>
        <Input
          id="full_name"
          type="text"
          autoComplete="name"
          placeholder="María García"
          aria-invalid={!!errors.full_name}
          aria-describedby={errors.full_name ? 'full-name-error' : undefined}
          {...register('full_name')}
        />
        {errors.full_name && (
          <p id="full-name-error" role="alert" className="text-xs text-red-600">
            {errors.full_name.message}
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
          placeholder="correo@aseguradora.com"
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
            autoComplete="new-password"
            placeholder="••••••••"
            aria-invalid={!!errors.password}
            aria-describedby={errors.password ? 'password-error' : 'password-hint'}
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
        {errors.password ? (
          <p id="password-error" role="alert" className="text-xs text-red-600">
            {errors.password.message}
          </p>
        ) : (
          <p id="password-hint" className="text-xs text-slate-500">
            Mínimo 8 caracteres, una mayúscula y un número.
          </p>
        )}
      </div>

      {/* Tenant slug */}
      <div className="space-y-1.5">
        <Label htmlFor="tenant_slug">Identificador de organización</Label>
        <Input
          id="tenant_slug"
          type="text"
          autoComplete="organization"
          placeholder="mi-aseguradora"
          aria-invalid={!!errors.tenant_slug}
          aria-describedby={
            errors.tenant_slug ? 'tenant-error' : 'tenant-hint'
          }
          {...register('tenant_slug')}
        />
        {errors.tenant_slug ? (
          <p id="tenant-error" role="alert" className="text-xs text-red-600">
            {errors.tenant_slug.message}
          </p>
        ) : (
          <p id="tenant-hint" className="text-xs text-slate-500">
            Código único de tu aseguradora (solo minúsculas, números y guiones).
          </p>
        )}
      </div>

      {/* Submit */}
      <Button
        type="submit"
        className="w-full"
        disabled={isSubmitting || !isValid}
        aria-busy={isSubmitting}
      >
        {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />}
        {isSubmitting ? 'Creando cuenta...' : 'Crear cuenta'}
      </Button>

      <p className="text-center text-sm text-slate-600">
        ¿Ya tenés una cuenta?{' '}
        <Link
          href="/login"
          className="font-medium text-blue-600 hover:underline focus-visible:underline focus-visible:outline-none"
        >
          Iniciar sesión
        </Link>
      </p>
    </form>
  )
}
