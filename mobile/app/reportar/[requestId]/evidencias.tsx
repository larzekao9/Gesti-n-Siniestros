import { useCallback, useState } from 'react'
import { Alert, ScrollView, Text, View } from 'react-native'
import { useFocusEffect, useLocalSearchParams, useRouter } from 'expo-router'
import { Camera, ImageIcon, Car, FileText } from 'lucide-react-native'
import type { LucideIcon } from 'lucide-react-native'

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
import { classifyDamage } from '@/lib/ml/damage'
import { checkPhotoQuality } from '@/lib/ml/quality'
import { colors } from '@/lib/theme'
import type { Evidence } from '@/types/evidence'

// Dos "sectores" de evidencia, cada uno con su propio análisis on-device:
//  - 'damage'   → fotos del vehículo → severidad (CU-35) + gate con "¿hay vehículo?" (CU-36)
//  - 'document' → papeles (parte/factura) → OCR (CU-34) + gate sin "¿hay vehículo?"
type Kind = 'damage' | 'document'

/** CU-36: aviso no bloqueante cuando la foto no pasa el gate de calidad.
 * Resuelve true si el asegurado decide subir igual (F-A1), false si toma otra. */
function confirmLowQuality(message: string): Promise<boolean> {
  return new Promise((resolve) => {
    Alert.alert(
      'Revisá la foto',
      message,
      [
        { text: 'Tomar otra', style: 'cancel', onPress: () => resolve(false) },
        { text: 'Subir igual', onPress: () => resolve(true) },
      ],
      { cancelable: false }
    )
  })
}

/** Una tarjeta de sector: icono + título + ayuda + botones + grilla de miniaturas. */
function SectorCard({
  icon: Icon,
  title,
  help,
  busy,
  evidences,
  pending,
  emptyLabel,
  onCamera,
  onGallery,
}: {
  icon: LucideIcon
  title: string
  help: string
  busy: boolean
  evidences: Evidence[]
  pending: LocalAsset[]
  emptyLabel: string
  onCamera: () => void
  onGallery: () => void
}) {
  const total = evidences.length + pending.length
  return (
    <View className="gap-3 rounded-2xl border border-line bg-white p-4">
      <View className="flex-row items-center gap-3">
        <View
          className="h-10 w-10 items-center justify-center rounded-full"
          style={{ backgroundColor: colors.line }}
        >
          <Icon size={20} color={colors.brand} />
        </View>
        <View className="flex-1">
          <Text className="text-base font-bold text-brand">{title}</Text>
          <Text className="mt-0.5 text-xs leading-4 text-muted">{help}</Text>
        </View>
      </View>

      <View className="flex-row gap-3">
        <View className="flex-1">
          <Button label="Tomar foto" icon={Camera} onPress={onCamera} variant="primary" disabled={busy} />
        </View>
        <View className="flex-1">
          <Button label="Galería" icon={ImageIcon} onPress={onGallery} variant="secondary" disabled={busy} />
        </View>
      </View>

      {total === 0 ? (
        <Text className="py-2 text-center text-xs text-muted">{emptyLabel}</Text>
      ) : (
        <View className="flex-row flex-wrap gap-2">
          {evidences.map((ev) => (
            <EvidenceThumb key={ev.id} uri={ev.download_url ?? ''} mimeType={ev.mime_type} />
          ))}
          {pending.map((p, i) => (
            <EvidenceThumb key={`p-${i}`} uri={p.uri} mimeType={p.mimeType} uploading />
          ))}
        </View>
      )}
    </View>
  )
}

export default function EvidenciasStep() {
  const { requestId } = useLocalSearchParams<{ requestId: string }>()
  const router = useRouter()
  const [evidences, setEvidences] = useState<Evidence[]>([])
  const [pending, setPending] = useState<Array<{ asset: LocalAsset; kind: Kind }>>([])
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<Kind | null>(null)

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

  async function handleAssets(assets: LocalAsset[], kind: Kind) {
    if (assets.length === 0) return
    setPending(assets.map((asset) => ({ asset, kind })))
    setBusy(kind)
    try {
      for (const asset of assets) {
        const metadata: Record<string, unknown> = {}
        // Los documentos se registran como 'other' (genérico, OCR-able); las fotos
        // del daño quedan como 'photo'. Así el analista y la IA saben qué es qué.
        const typedAsset: LocalAsset = kind === 'document' ? { ...asset, type: 'other' } : asset

        if (asset.type === 'photo' || asset.type === 'other') {
          // CU-36: gate de calidad. Para documentos se apaga el "¿hay vehículo?".
          const quality = await checkPhotoQuality(asset.uri, { vehicleCheck: kind === 'damage' })
          if (!quality.ok && !(await confirmLowQuality(quality.message))) continue

          if (kind === 'damage') {
            // CU-35: severidad on-device (solo fotos del vehículo).
            const damage = await classifyDamage(asset.uri)
            if (damage) metadata.damage_classification = damage
          } else {
            // CU-34: OCR on-device (solo documentos).
            const ocrText = await extractText(asset.uri)
            if (ocrText) metadata.ocr_text = ocrText
          }
        }

        await uploadRequestEvidence(
          requestId,
          typedAsset,
          Object.keys(metadata).length > 0 ? metadata : undefined
        )
      }
      await refresh()
    } catch {
      Alert.alert('No se pudo subir', 'Revisá tu conexión e intentá de nuevo.')
    } finally {
      setPending([])
      setBusy(null)
    }
  }

  async function pickFor(kind: Kind, source: 'camera' | 'gallery') {
    try {
      if (source === 'camera') {
        const asset = await captureFromCamera()
        if (asset) await handleAssets([asset], kind)
      } else {
        const assets = await pickFromGallery()
        await handleAssets(assets, kind)
      }
    } catch (err) {
      Alert.alert(source === 'camera' ? 'Cámara' : 'Galería', (err as Error).message)
    }
  }

  if (loading) return <Loading label="Cargando evidencias…" />

  // Separar las evidencias ya subidas por sector.
  const damageEvidences = evidences.filter((e) => e.type === 'photo')
  const docEvidences = evidences.filter(
    (e) => e.type !== 'photo' && e.mime_type.startsWith('image/')
  )
  const pendingDamage = pending.filter((p) => p.kind === 'damage').map((p) => p.asset)
  const pendingDocs = pending.filter((p) => p.kind === 'document').map((p) => p.asset)

  return (
    <Screen edges={['bottom']}>
      <ScrollView contentContainerStyle={{ padding: 20, gap: 20 }}>
        <WizardStepper current={2} />

        <View>
          <Text className="text-lg font-bold text-brand">Adjuntá las evidencias</Text>
          <Text className="mt-1 text-sm leading-5 text-muted">
            Separá las fotos del vehículo de los documentos. Necesitás al menos una foto del
            daño para poder enviar la solicitud.
          </Text>
        </View>

        <SectorCard
          icon={Car}
          title="Fotos del vehículo"
          help="Sacá fotos del auto y los daños: frente, lateral, lo que se vea afectado."
          busy={busy === 'damage'}
          evidences={damageEvidences}
          pending={pendingDamage}
          emptyLabel="Todavía no subiste fotos del daño"
          onCamera={() => pickFor('damage', 'camera')}
          onGallery={() => pickFor('damage', 'gallery')}
        />

        <SectorCard
          icon={FileText}
          title="Documentos"
          help="Parte de tránsito, facturas u otros papeles (opcional). Leemos el texto automáticamente."
          busy={busy === 'document'}
          evidences={docEvidences}
          pending={pendingDocs}
          emptyLabel="Sin documentos adjuntos"
          onCamera={() => pickFor('document', 'camera')}
          onGallery={() => pickFor('document', 'gallery')}
        />

        {/* CU-33: análisis de daño por foto (IA), solo sobre las fotos del vehículo. */}
        {damageEvidences.length > 0 ? (
          <View className="gap-3">
            <View>
              <Text className="text-base font-bold text-brand">Análisis de daño con IA</Text>
              <Text className="mt-1 text-xs leading-4 text-muted">
                Opcional: la IA estima la severidad del daño de cada foto. No afecta el envío de
                tu solicitud.
              </Text>
            </View>
            {damageEvidences.map((ev) => (
              <DamageAnalysisCard key={ev.id} requestId={requestId} evidence={ev} />
            ))}
          </View>
        ) : null}

        <View className="mt-2">
          <Button
            label="Continuar"
            onPress={() => router.push(`/reportar/${requestId}/confirmar`)}
            disabled={!!busy || damageEvidences.length === 0}
          />
          {damageEvidences.length === 0 ? (
            <Text className="mt-2 text-center text-xs text-muted">
              Subí al menos una foto del daño para continuar.
            </Text>
          ) : null}
        </View>
      </ScrollView>
    </Screen>
  )
}
