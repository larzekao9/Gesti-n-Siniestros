import { useState } from 'react'
import { Pressable, Text, View } from 'react-native'
import { Link } from 'expo-router'
import { Controller, useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { MailCheck } from 'lucide-react-native'

import { AuthShell } from '@/components/auth/AuthShell'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { forgotPassword } from '@/lib/api/insured-auth'
import { apiErrorMessage } from '@/lib/api/client'
import { colors } from '@/lib/theme'
import { forgotPasswordSchema, type ForgotPasswordValues } from '@/lib/validations/auth'

export default function ForgotPasswordScreen() {
  const [sent, setSent] = useState(false)
  const [loading, setLoading] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

  const { control, handleSubmit, formState: { errors } } = useForm<ForgotPasswordValues>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: { tenant_slug: '', email: '' },
  })

  async function onSubmit(values: ForgotPasswordValues) {
    setSubmitError(null)
    setLoading(true)
    try {
      await forgotPassword(values)
      setSent(true)
    } catch (err) {
      setSubmitError(apiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  if (sent) {
    return (
      <AuthShell title="Revisá tu correo">
        <View className="items-center gap-3 py-6">
          <View className="h-16 w-16 items-center justify-center rounded-full bg-accent-50">
            <MailCheck size={30} color={colors.accent} />
          </View>
          <Text className="text-center text-sm leading-5 text-muted">
            Si el email está registrado, te enviamos instrucciones para restablecer tu
            contraseña.
          </Text>
        </View>
        <Link href="/(auth)/login" asChild>
          <Pressable>
            <Button label="Volver a iniciar sesión" variant="secondary" />
          </Pressable>
        </Link>
      </AuthShell>
    )
  }

  return (
    <AuthShell
      title="Recuperar contraseña"
      subtitle="Te enviaremos instrucciones al email de tu cuenta."
    >
      <Controller
        control={control}
        name="tenant_slug"
        render={({ field: { onChange, onBlur, value } }) => (
          <Input
            label="Aseguradora"
            placeholder="ej. aseguradora-a"
            autoCapitalize="none"
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
            value={value}
            onBlur={onBlur}
            onChangeText={onChange}
            error={errors.email?.message}
            required
          />
        )}
      />

      {submitError ? (
        <View className="rounded-xl bg-danger-50 px-4 py-3">
          <Text className="text-sm text-danger">{submitError}</Text>
        </View>
      ) : null}

      <Button label="Enviar instrucciones" onPress={handleSubmit(onSubmit)} loading={loading} />

      <View className="mt-1 items-center pb-8">
        <Link href="/(auth)/login" asChild>
          <Pressable hitSlop={8}>
            <Text className="text-sm font-medium text-accent">Volver</Text>
          </Pressable>
        </Link>
      </View>
    </AuthShell>
  )
}
