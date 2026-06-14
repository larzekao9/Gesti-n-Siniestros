import { useCallback, useState } from 'react'
import { Alert, ScrollView, Text, View } from 'react-native'
import { useFocusEffect, useLocalSearchParams, useRouter } from 'expo-router'
import { Camera, ImageIcon } from 'lucide-react-native'

import { Button } from '@/components/ui/Button'
import { Loading } from '@/components/ui/Loading'
import { Screen } from '@/components/ui/Screen'
import { WizardStepper } from '@/components/claim-requests/WizardStepper'
import { EvidenceThumb } from '@/components/claim-requests/EvidenceThumb'
import { DamageAnalysisCard } from '@/components/claim-requests/DamageAnalysisCard'
import {
  listRequestEvidences,
  uploadRequestEvidence,
  type LocalAsset,
} from '@/lib/api/evidences'
import { captureFromCamera, pickFromGallery } from '@/lib/utils/media'
import { extractText } from '@/lib/utils/ocr'
import { colors } from '@/lib/theme'
import type { Evidence } from '@/types/evidence'

export default function EvidenciasStep() {
  const { requestId } = useLocalSearchParams<{ requestId: string }>()
  const router = useRouter()
  const [evidences, setEvidences] = useState<Evidence[]>([])
  const [pending, setPending] = useState<LocalAsset[]>([])
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)

  const refresh = useCallback(async () => {
    try {
      const data = await listRequestEvidences(requestId)
      setEvidences(data.items)
    } catch {
      // se mostrará vacío; el usuario puede reintentar
    } finally {
      setLoading(false)
    }
  }, [requestId])

  useFocusEffect(
    useCallback(() => {
      refresh()
    }, [refresh])
  )

  async function handleAssets(assets: LocalAsset[]) {
    if (assets.length === 0) return
    setPending(assets)
    setBusy(true)
    try {
      for (const asset of assets) {
        // CU-34: OCR on-device de imágenes (parte/factura). Si no hay texto o el
        // nativo no está disponible (Expo Go), devuelve '' y se sube sin metadata.
        const ocrText =
          asset.type === 'photo' ? await extractText(asset.uri) : ''
        await uploadRequestEvidence(
          requestId,
          asset,
          ocrText ? { ocr_text: ocrText } : undefined
        )
      }
      await refresh()
    } catch (err) {
      Alert.alert('No se pudo subir', 'Revisá tu conexión e intentá de nuevo.')
    } finally {
      setPending([])
      setBusy(false)
    }
  }

  async function onCamera() {
    try {
      const asset = await captureFromCamera()
      if (asset) await handleAssets([asset])
    } catch (err) {
      Alert.alert('Cámara', (err as Error).message)
    }
  }

  async function onGallery() {
    try {
      const assets = await pickFromGallery()
      await handleAssets(assets)
    } catch (err) {
      Alert.alert('Galería', (err as Error).message)
    }
  }

  if (loading) return <Loading label="Cargando evidencias…" />

  const total = evidences.length + pending.length

  return (
    <Screen edges={['bottom']}>
      <ScrollView contentContainerStyle={{ padding: 20, gap: 16 }}>
        <WizardStepper current={2} />

        <View>
          <Text className="text-lg font-bold text-brand">Adjuntá fotos del siniestro</Text>
          <Text className="mt-1 text-sm leading-5 text-muted">
            Sumá fotos del lugar y de los daños. Necesitás al menos una para poder enviar
            la solicitud.
          </Text>
        </View>

        <View className="flex-row gap-3">
          <View className="flex-1">
            <Button label="Tomar foto" icon={Camera} onPress={onCamera} variant="primary" />
          </View>
          <View className="flex-1">
            <Button label="Galería" icon={ImageIcon} onPress={onGallery} variant="secondary" />
          </View>
        </View>

        {total === 0 ? (
          <View className="items-center rounded-2xl border border-dashed border-line bg-white py-10">
            <Camera size={28} color={colors.mutedFg} />
            <Text className="mt-2 text-sm text-muted">Todavía no subiste evidencias</Text>
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
            {pending.map((p, i) => (
              <EvidenceThumb key={`pending-${i}`} uri={p.uri} mimeType={p.mimeType} uploading />
            ))}
          </View>
        )}

        {/* CU-33: análisis de daño por foto (IA). Apoyo informativo opcional. */}
        {evidences.some((ev) => ev.mime_type.startsWith('image/')) ? (
          <View className="gap-3">
            <View>
              <Text className="text-base font-bold text-brand">Análisis de daño con IA</Text>
              <Text className="mt-1 text-xs leading-4 text-muted">
                Opcional: la IA estima el tipo y la severidad del daño de cada foto. No
                afecta el envío de tu solicitud.
              </Text>
            </View>
            {evidences
              .filter((ev) => ev.mime_type.startsWith('image/'))
              .map((ev) => (
                <DamageAnalysisCard key={ev.id} requestId={requestId} evidence={ev} />
              ))}
          </View>
        ) : null}

        <View className="mt-2">
          <Button
            label="Continuar"
            onPress={() => router.push(`/reportar/${requestId}/confirmar`)}
            disabled={busy || evidences.length === 0}
          />
          {evidences.length === 0 ? (
            <Text className="mt-2 text-center text-xs text-muted">
              Subí al menos una foto para continuar.
            </Text>
          ) : null}
        </View>
      </ScrollView>
    </Screen>
  )
}
