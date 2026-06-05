import { ScrollView, Text, View } from 'react-native'
import { Stack, useLocalSearchParams } from 'expo-router'
import { AlertTriangle, CalendarDays, FileText, MapPin } from 'lucide-react-native'

import { Card } from '@/components/ui/Card'
import { Loading } from '@/components/ui/Loading'
import { Screen } from '@/components/ui/Screen'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { useMyClaimRequest } from '@/lib/hooks/useClaims'
import { colors } from '@/lib/theme'
import { formatDate } from '@/lib/utils/format'

export default function SolicitudDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>()
  const { data: req, isLoading } = useMyClaimRequest(id)

  if (isLoading) return <Loading label="Cargando solicitud…" />
  if (!req) {
    return (
      <Screen>
        <View className="flex-1 items-center justify-center p-8">
          <Text className="text-center text-muted">No encontramos esta solicitud.</Text>
        </View>
      </Screen>
    )
  }

  const rejected = req.status === 'rejected_at_intake'

  return (
    <Screen edges={['bottom']}>
      <Stack.Screen options={{ title: req.request_number ?? 'Solicitud' }} />
      <ScrollView contentContainerStyle={{ padding: 20, paddingBottom: 40, gap: 16 }}>
        <View className="gap-2">
          <Text className="text-xs font-medium uppercase tracking-wide text-muted">
            Solicitud
          </Text>
          <Text className="text-2xl font-bold text-brand">
            {req.request_number ?? 'Sin número'}
          </Text>
          <StatusBadge status={req.status} />
        </View>

        {rejected && req.intake_decision_reason ? (
          <View className="flex-row items-start gap-3 rounded-xl bg-danger-50 p-4">
            <AlertTriangle size={20} color={colors.danger} />
            <View className="flex-1">
              <Text className="text-sm font-semibold text-danger">Solicitud rechazada</Text>
              <Text className="mt-1 text-sm leading-5 text-brand">
                {req.intake_decision_reason}
              </Text>
            </View>
          </View>
        ) : (
          <View className="rounded-xl bg-info-50 p-3">
            <Text className="text-xs leading-4 text-info">
              Tu solicitud está siendo revisada por un analista. Te avisaremos cuando haya
              novedades.
            </Text>
          </View>
        )}

        <Card className="gap-3">
          <View className="flex-row items-start gap-3">
            <CalendarDays size={18} color={colors.muted} />
            <View className="flex-1">
              <Text className="text-xs text-muted">Fecha del accidente</Text>
              <Text className="text-base text-brand">{formatDate(req.accident_date)}</Text>
            </View>
          </View>
          <View className="h-px bg-line" />
          <View className="flex-row items-start gap-3">
            <MapPin size={18} color={colors.muted} />
            <View className="flex-1">
              <Text className="text-xs text-muted">Lugar</Text>
              <Text className="text-base text-brand">{req.accident_location ?? '—'}</Text>
            </View>
          </View>
          {req.accident_description ? (
            <>
              <View className="h-px bg-line" />
              <View className="flex-row items-start gap-3">
                <FileText size={18} color={colors.muted} />
                <View className="flex-1">
                  <Text className="text-xs text-muted">Descripción</Text>
                  <Text className="text-base leading-5 text-brand">
                    {req.accident_description}
                  </Text>
                </View>
              </View>
            </>
          ) : null}
        </Card>
      </ScrollView>
    </Screen>
  )
}
