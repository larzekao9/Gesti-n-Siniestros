import { useState } from 'react'
import { Pressable, Text, View } from 'react-native'
import { Link, useRouter } from 'expo-router'
import { Controller, useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'

import { AuthShell } from '@/components/auth/AuthShell'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { login } from '@/lib/api/insured-auth'
import { apiErrorMessage } from '@/lib/api/client'
import { useAuthStore } from '@/lib/stores/authStore'
import { insuredLoginSchema, type InsuredLoginValues } from '@/lib/validations/auth'

export default function LoginScreen() {
  const router = useRouter()
  const setSession = useAuthStore((s) => s.setSession)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const { control, handleSubmit, formState: { errors } } = useForm<InsuredLoginValues>({
    resolver: zodResolver(insuredLoginSchema),
    defaultValues: { tenant_slug: '', email: '', password: '' },
  })

  async function onSubmit(values: InsuredLoginValues) {
    setSubmitError(null)
    setLoading(true)
    try {
      const resp = await login(values)
      await setSession({
        account: resp.account,
        accessToken: resp.access_token,
        refreshToken: resp.refresh_token,
        tenantSlug: values.tenant_slug,
      })
      router.replace('/(tabs)')
    } catch (err) {
      setSubmitError(apiErrorMessage(err, 'No se pudo iniciar sesión'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell title="Ingresá a tu cuenta" subtitle="Seguí el estado de tus reclamos y reportá nuevos siniestros.">
      <Controller
        control={control}
        name="tenant_slug"
        render={({ field: { onChange, onBlur, value } }) => (
          <Input
            label="Aseguradora"
            placeholder="ej. aseguradora-a"
            autoCapitalize="none"
            autoCorrect={false}
            value={value}
            onBlur={onBlur}
            onChangeText={onChange}
            error={errors.tenant_slug?.message}
            required
          />
        )}
      />
      <Controller
        control={control}
        name="email"
        render={({ field: { onChange, onBlur, value } }) => (
          <Input
            label="Email"
            placeholder="tu@email.com"
            autoCapitalize="none"
            keyboardType="email-address"
            autoComplete="email"
            value={value}
            onBlur={onBlur}
            onChangeText={onChange}
            error={errors.email?.message}
            required
          />
        )}
      />
      <Controller
        control={control}
        name="password"
        render={({ field: { onChange, onBlur, value } }) => (
          <Input
            label="Contraseña"
            placeholder="••••••••"
            secureTextEntry
            autoComplete="password"
            value={value}
            onBlur={onBlur}
            onChangeText={onChange}
            error={errors.password?.message}
            required
          />
        )}
      />

      {submitError ? (
        <View className="rounded-xl bg-danger-50 px-4 py-3">
          <Text className="text-sm text-danger">{submitError}</Text>
        </View>
      ) : null}

      <Button label="Ingresar" onPress={handleSubmit(onSubmit)} loading={loading} />

      <View className="mt-1 items-center gap-3 pb-8">
        <Link href="/(auth)/forgot-password" asChild>
          <Pressable hitSlop={8}>
            <Text className="text-sm font-medium text-accent">¿Olvidaste tu contraseña?</Text>
          </Pressable>
        </Link>
        <View className="flex-row items-center gap-1">
          <Text className="text-sm text-muted">¿Tenés un código de invitación?</Text>
          <Link href="/(auth)/register" asChild>
            <Pressable hitSlop={8}>
              <Text className="text-sm font-semibold text-accent">Activá tu cuenta</Text>
            </Pressable>
          </Link>
        </View>
      </View>
    </AuthShell>
  )
}
