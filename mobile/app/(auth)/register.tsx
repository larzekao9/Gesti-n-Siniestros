import { useState } from 'react'
import { Pressable, Text, View } from 'react-native'
import { Link, useLocalSearchParams, useRouter } from 'expo-router'
import { Controller, useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'

import { AuthShell } from '@/components/auth/AuthShell'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { registerWithToken } from '@/lib/api/insured-auth'
import { apiErrorMessage } from '@/lib/api/client'
import { useAuthStore } from '@/lib/stores/authStore'
import {
  registerWithTokenSchema,
  type RegisterWithTokenValues,
} from '@/lib/validations/auth'

export default function RegisterScreen() {
  const router = useRouter()
  const params = useLocalSearchParams<{ token?: string; tenant?: string }>()
  const setSession = useAuthStore((s) => s.setSession)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const { control, handleSubmit, formState: { errors } } = useForm<RegisterWithTokenValues>({
    resolver: zodResolver(registerWithTokenSchema),
    defaultValues: {
      activation_token: params.token ?? '',
      password: '',
      confirm_password: '',
    },
  })

  async function onSubmit(values: RegisterWithTokenValues) {
    setSubmitError(null)
    setLoading(true)
    try {
      const resp = await registerWithToken({
        activation_token: values.activation_token,
        password: values.password,
      })
      await setSession({
        account: resp.account,
        accessToken: resp.access_token,
        refreshToken: resp.refresh_token,
        // El tenant slug del deep link, o se completa luego en el próximo login.
        tenantSlug: params.tenant ?? '',
      })
      router.replace('/(tabs)')
    } catch (err) {
      setSubmitError(apiErrorMessage(err, 'No se pudo activar la cuenta'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell
      title="Activá tu cuenta"
      subtitle="Ingresá el código de invitación que te dio tu aseguradora y elegí una contraseña."
    >
      <Controller
        control={control}
        name="activation_token"
        render={({ field: { onChange, onBlur, value } }) => (
          <Input
            label="Código de activación"
            placeholder="Pegá el código de invitación"
            autoCapitalize="none"
            autoCorrect={false}
            value={value}
            onBlur={onBlur}
            onChangeText={onChange}
            error={errors.activation_token?.message}
            required
          />
        )}
      />
      <Controller
        control={control}
        name="password"
        render={({ field: { onChange, onBlur, value } }) => (
          <Input
            label="Nueva contraseña"
            placeholder="Mínimo 8, con mayúscula y número"
            secureTextEntry
            value={value}
            onBlur={onBlur}
            onChangeText={onChange}
            error={errors.password?.message}
            helper="Al menos 8 caracteres, una mayúscula y un número."
            required
          />
        )}
      />
      <Controller
        control={control}
        name="confirm_password"
        render={({ field: { onChange, onBlur, value } }) => (
          <Input
            label="Confirmar contraseña"
            placeholder="Repetí la contraseña"
            secureTextEntry
            value={value}
            onBlur={onBlur}
            onChangeText={onChange}
            error={errors.confirm_password?.message}
            required
          />
        )}
      />

      {submitError ? (
        <View className="rounded-xl bg-danger-50 px-4 py-3">
          <Text className="text-sm text-danger">{submitError}</Text>
        </View>
      ) : null}

      <Button label="Activar y entrar" onPress={handleSubmit(onSubmit)} loading={loading} />

      <View className="mt-1 flex-row items-center justify-center gap-1 pb-8">
        <Text className="text-sm text-muted">¿Ya tenés cuenta?</Text>
        <Link href="/(auth)/login" asChild>
          <Pressable hitSlop={8}>
            <Text className="text-sm font-semibold text-accent">Iniciá sesión</Text>
          </Pressable>
        </Link>
      </View>
    </AuthShell>
  )
}
