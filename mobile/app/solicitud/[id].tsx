import { useState } from 'react'
import { Alert, ScrollView, Text, View } from 'react-native'
import { Stack, useLocalSearchParams } from 'expo-router'
import { useQueryClient } from '@tanstack/react-query'
import {
  AlertTriangle,
  CalendarDays,
  Camera,
  FileText,
  ImageIcon,
  MapPin,
} from 'lucide-react-native'

import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Loading } from '@/components/ui/Loading'
import { Screen } from '@/components/ui/Screen'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { EvidenceThumb } from '@/components/claim-requests/EvidenceThumb'
import {
  claimKeys,
  useMyClaimRequest,
  useRequestEvidences,
} from '@/lib/hooks/useClaims'
import { uploadRequestEvidence, type LocalAsset } from '@/lib/api/evidences'
import { captureFromCamera, pickFromGallery } from '@/lib/utils/media'
import { colors } from '@/lib/theme'
import { formatDate } from '@/lib/utils/format'

export default function SolicitudDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>()
  const { data: req, isLoading } = useMyClaimRequest(id)
  const { data: evidenceData } = useRequestEvidences(id)
  const qc = useQueryClient()
  const [busy, setBusy] = useState(false)

  const evidences = evidenceData?.items ?? []
  // El backend acepta evidencias mientras la solicitud no esté formalizada ni
  // rechazada (evidence_service). En el detalle solo llegan submitted /
  // under_intake_review / rejected, así que habilitamos en los dos primeros.
  const canAddEvidence =
    req?.status === 'submitted' || req?.status === 'under_intake_review'

  async function uploadAssets(assets: LocalAsset[]) {
    if (!id || assets.length === 0) return
    setBusy(true)
    try {
      for (const asset of assets) {
        await uploadRequestEvidence(id, asset)
      }
      await qc.invalidateQueries({ queryKey: claimKeys.requestEvidences(id) })
    } catch {
      Alert.alert('No se pudo subir', 'Revisá tu conexión e intentá de nuevo.')
    } finally {
      setBusy(false)
    }
  }

  async function onCamera() {
    try {
      const asset = await captureFromCamera()
      if (asset) await uploadAssets([asset])
    } catch (err) {
      Alert.alert('Cámara', (err as Error).message)
    }
  }

  async function onGallery() {
    try {
      const assets = await pickFromGallery()
      await uploadAssets(assets)
    } catch (err) {
      Alert.alert('Galería', (err as Error).message)
    }
  }

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

        <View className="gap-3">
          <View className="flex-row items-center justify-between">
            <Text className="text-base font-bold text-brand">Evidencias</Text>
            <Text className="text-xs text-muted">
              {evidences.length} {evidences.length === 1 ? 'archivo' : 'archivos'}
            </Text>
          </View>

          {evidences.length === 0 ? (
            <View className="items-center rounded-2xl border border-dashed border-line bg-white py-8">
              <FileText size={26} color={colors.mutedFg} />
              <Text className="mt-2 text-sm text-muted">No hay evidencias cargadas</Text>
            </View>
          ) : (
            <View className="flex-row flex-wrap gap-3">
              {evidences.map((ev) => (
                <EvidenceThumb
                  key={ev.id}
                  uri={ev.download_url ?? ''}
                  mimeType={ev.mime_type}
                />
              ))}
            </View>
          )}

          {canAddEvidence ? (
            <View className="flex-row gap-3">
              <View className="flex-1">
                <Button
                  label="Tomar foto"
                  icon={Camera}
                  variant="secondary"
                  onPress={onCamera}
                  loading={busy}
                />
              </View>
              <View className="flex-1">
                <Button
                  label="Galería"
                  icon={ImageIcon}
                  variant="secondary"
                  onPress={onGallery}
                  loading={busy}
                />
              </View>
            </View>
          ) : null}
        </View>
      </ScrollView>
    </Screen>
  )
}
