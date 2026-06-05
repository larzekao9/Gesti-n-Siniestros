import { useState } from 'react'
import { ScrollView, Text, View } from 'react-native'
import { useLocalSearchParams, useRouter } from 'expo-router'
import { CalendarDays, CheckCircle2, FileText, MapPin } from 'lucide-react-native'

import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Loading } from '@/components/ui/Loading'
import { Screen } from '@/components/ui/Screen'
import { WizardStepper } from '@/components/claim-requests/WizardStepper'
import { apiErrorMessage } from '@/lib/api/client'
import { useMyClaimRequest } from '@/lib/hooks/useClaims'
import { useSubmitClaimRequest } from '@/lib/hooks/useDraft'
import { colors } from '@/lib/theme'
import { formatDate } from '@/lib/utils/format'

export default function ConfirmarStep() {
  const { requestId } = useLocalSearchParams<{ requestId: string }>()
  const router = useRouter()
  const { data: draft, isLoading } = useMyClaimRequest(requestId)
  const submit = useSubmitClaimRequest()

  const [submitted, setSubmitted] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function onSubmit() {
    setError(null)
    try {
      const result = await submit.mutateAsync(requestId)
      setSubmitted(result.request_number ?? 'enviada')
    } catch (err) {
      setError(apiErrorMessage(err, 'No se pudo enviar la solicitud'))
    }
  }

  if (isLoading) return <Loading />

  if (submitted) {
    return (
      <Screen>
        <View className="flex-1 items-center justify-center gap-4 px-8">
          <View className="h-20 w-20 items-center justify-center rounded-full bg-accent-50">
            <CheckCircle2 size={40} color={colors.accent} />
          </View>
          <Text className="text-center text-2xl font-bold text-brand">¡Solicitud enviada!</Text>
          <Text className="text-center text-sm leading-5 text-muted">
            Tu solicitud{' '}
            <Text className="font-semibold text-brand">{submitted}</Text> fue enviada. Un
            analista la revisará y te avisaremos por una notificación.
          </Text>
          <View className="mt-4 w-full">
            <Button label="Volver al inicio" onPress={() => router.replace('/(tabs)')} />
          </View>
        </View>
      </Screen>
    )
  }

  return (
    <Screen edges={['bottom']}>
      <ScrollView contentContainerStyle={{ padding: 20, gap: 16 }}>
        <WizardStepper current={3} />

        <Text className="text-lg font-bold text-brand">Revisá y enviá</Text>

        <Card className="gap-4">
          <View className="flex-row items-start gap-3">
            <CalendarDays size={18} color={colors.muted} />
            <View className="flex-1">
              <Text className="text-xs text-muted">Fecha del accidente</Text>
              <Text className="text-base text-brand">{formatDate(draft?.accident_date)}</Text>
            </View>
          </View>
          <View className="h-px bg-line" />
          <View className="flex-row items-start gap-3">
            <MapPin size={18} color={colors.muted} />
            <View className="flex-1">
              <Text className="text-xs text-muted">Lugar</Text>
              <Text className="text-base text-brand">{draft?.accident_location ?? '—'}</Text>
            </View>
          </View>
          <View className="h-px bg-line" />
          <View className="flex-row items-start gap-3">
            <FileText size={18} color={colors.muted} />
            <View className="flex-1">
              <Text className="text-xs text-muted">Descripción</Text>
              <Text className="text-base leading-5 text-brand">
                {draft?.accident_description ?? '—'}
              </Text>
            </View>
          </View>
        </Card>

        <View className="rounded-xl bg-info-50 p-3">
          <Text className="text-xs leading-4 text-info">
            Al enviar, tu solicitud entra a revisión. No vas a poder editarla, pero podés
            seguir su estado desde "Mis reclamos".
          </Text>
        </View>

        {error ? <Text className="text-sm text-danger">{error}</Text> : null}

        <Button
          label="Enviar solicitud"
          onPress={onSubmit}
          loading={submit.isPending}
        />
      </ScrollView>
    </Screen>
  )
}
