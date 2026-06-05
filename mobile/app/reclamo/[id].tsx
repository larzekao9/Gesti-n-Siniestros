import { ScrollView, Text, View } from 'react-native'
import { Stack, useLocalSearchParams } from 'expo-router'
import { Car, FileText, MapPin, MessageSquare } from 'lucide-react-native'

import { Card } from '@/components/ui/Card'
import { Loading } from '@/components/ui/Loading'
import { Screen } from '@/components/ui/Screen'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { ClaimStatusTimeline } from '@/components/claim-requests/ClaimStatusTimeline'
import { DocumentRequestItem } from '@/components/claim-requests/DocumentRequestItem'
import { useMyClaim } from '@/lib/hooks/useClaims'
import { colors } from '@/lib/theme'
import { formatDate, formatDateTime } from '@/lib/utils/format'

function SectionTitle({ children }: { children: string }) {
  return <Text className="mb-3 mt-6 text-base font-bold text-brand">{children}</Text>
}

export default function ClaimDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>()
  const { data: claim, isLoading } = useMyClaim(id)

  if (isLoading) return <Loading label="Cargando expediente…" />
  if (!claim) {
    return (
      <Screen>
        <View className="flex-1 items-center justify-center p-8">
          <Text className="text-center text-muted">No encontramos este reclamo.</Text>
        </View>
      </Screen>
    )
  }

  const pendingDocs = claim.document_requests.filter((d) => d.status === 'pending')

  return (
    <Screen edges={['bottom']}>
      <Stack.Screen options={{ title: claim.claim_number }} />
      <ScrollView contentContainerStyle={{ padding: 20, paddingBottom: 40 }}>
        {/* Header */}
        <View className="gap-2">
          <Text className="text-xs font-medium uppercase tracking-wide text-muted">
            Expediente
          </Text>
          <Text className="text-2xl font-bold text-brand">{claim.claim_number}</Text>
          <StatusBadge status={claim.status} />
        </View>

        {claim.decision ? (
          <View
            className="mt-4 rounded-xl p-4"
            style={{
              backgroundColor: claim.decision === 'approved' ? colors.accent50 : colors.danger50,
            }}
          >
            <Text
              className="text-sm font-semibold"
              style={{ color: claim.decision === 'approved' ? '#15803D' : '#B91C1C' }}
            >
              {claim.decision === 'approved' ? 'Expediente aprobado' : 'Expediente rechazado'}
            </Text>
            {claim.decision_reason ? (
              <Text className="mt-1 text-sm text-brand">{claim.decision_reason}</Text>
            ) : null}
          </View>
        ) : null}

        {/* Vehículo / póliza */}
        <Card className="mt-5 gap-3">
          <View className="flex-row items-center gap-2">
            <Car size={18} color={colors.brand} />
            <Text className="font-semibold text-brand">
              {claim.vehicle ? `${claim.vehicle.make} ${claim.vehicle.model} ${claim.vehicle.year}` : 'Vehículo'}
            </Text>
          </View>
          {claim.vehicle ? (
            <Text className="text-xs text-muted">Placa {claim.vehicle.plate}</Text>
          ) : null}
          {claim.policy ? (
            <Text className="text-xs text-muted">
              Póliza {claim.policy.policy_number} · {claim.policy.coverage_type}
            </Text>
          ) : null}
        </Card>

        {/* Datos del accidente */}
        <Card className="mt-3 gap-3">
          <View className="flex-row items-start gap-3">
            <MapPin size={18} color={colors.muted} />
            <View className="flex-1">
              <Text className="text-xs text-muted">Lugar y fecha</Text>
              <Text className="text-base text-brand">{claim.accident_location}</Text>
              <Text className="text-xs text-muted">{formatDate(claim.accident_date)}</Text>
            </View>
          </View>
          {claim.accident_description ? (
            <View className="flex-row items-start gap-3">
              <FileText size={18} color={colors.muted} />
              <View className="flex-1">
                <Text className="text-xs text-muted">Descripción</Text>
                <Text className="text-base leading-5 text-brand">
                  {claim.accident_description}
                </Text>
              </View>
            </View>
          ) : null}
        </Card>

        {/* Documentación pendiente (CU-07/08) */}
        {claim.document_requests.length > 0 ? (
          <>
            <SectionTitle>
              {pendingDocs.length > 0
                ? `Documentación pendiente (${pendingDocs.length})`
                : 'Documentación'}
            </SectionTitle>
            <View className="gap-3">
              {claim.document_requests.map((doc) => (
                <DocumentRequestItem key={doc.id} doc={doc} claimId={claim.id} />
              ))}
            </View>
          </>
        ) : null}

        {/* Observaciones públicas */}
        {claim.observations.length > 0 ? (
          <>
            <SectionTitle>Comentarios del analista</SectionTitle>
            <View className="gap-3">
              {claim.observations.map((o) => (
                <Card key={o.id} className="flex-row gap-3">
                  <MessageSquare size={18} color={colors.muted} />
                  <View className="flex-1">
                    <Text className="text-sm leading-5 text-brand">{o.comment}</Text>
                    <Text className="mt-1 text-xs text-muted-fg">
                      {formatDateTime(o.created_at)}
                    </Text>
                  </View>
                </Card>
              ))}
            </View>
          </>
        ) : null}

        {/* Línea de tiempo */}
        <SectionTitle>Historial</SectionTitle>
        <Card>
          <ClaimStatusTimeline entries={claim.timeline} />
        </Card>
      </ScrollView>
    </Screen>
  )
}
