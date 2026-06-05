import { useState } from 'react'
import { ActionSheetIOS, Alert, Platform, Text, View } from 'react-native'
import { useQueryClient } from '@tanstack/react-query'
import { CheckCircle2, Clock, Paperclip } from 'lucide-react-native'

import { Button } from '@/components/ui/Button'
import { submitDocument } from '@/lib/api/evidences'
import { captureFromCamera, pickFromGallery } from '@/lib/utils/media'
import { claimKeys } from '@/lib/hooks/useClaims'
import { colors } from '@/lib/theme'
import type { InsuredDocumentRequest } from '@/types/claim'

// Item de documentación solicitada (CU-07) con acción de adjuntar (CU-08).
export function DocumentRequestItem({
  doc,
  claimId,
}: {
  doc: InsuredDocumentRequest
  claimId: string
}) {
  const qc = useQueryClient()
  const [busy, setBusy] = useState(false)
  const isPending = doc.status === 'pending'

  async function upload(source: 'camera' | 'gallery') {
    setBusy(true)
    try {
      const assets =
        source === 'camera'
          ? [await captureFromCamera()].filter(Boolean)
          : await pickFromGallery()
      const asset = (assets as any[])[0]
      if (!asset) return
      await submitDocument(doc.id, asset)
      await qc.invalidateQueries({ queryKey: claimKeys.claim(claimId) })
      Alert.alert('Documento enviado', 'Tu documentación fue adjuntada correctamente.')
    } catch (err) {
      Alert.alert('No se pudo adjuntar', (err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  function chooseSource() {
    if (Platform.OS === 'ios') {
      ActionSheetIOS.showActionSheetWithOptions(
        { options: ['Cancelar', 'Tomar foto', 'Elegir de galería'], cancelButtonIndex: 0 },
        (i) => {
          if (i === 1) upload('camera')
          else if (i === 2) upload('gallery')
        }
      )
    } else {
      Alert.alert('Adjuntar documento', undefined, [
        { text: 'Tomar foto', onPress: () => upload('camera') },
        { text: 'Elegir de galería', onPress: () => upload('gallery') },
        { text: 'Cancelar', style: 'cancel' },
      ])
    }
  }

  return (
    <View className="gap-2 rounded-xl border border-line bg-white p-4">
      <View className="flex-row items-start gap-2">
        {isPending ? (
          <Clock size={18} color={colors.warning} />
        ) : (
          <CheckCircle2 size={18} color={colors.accent} />
        )}
        <Text className="flex-1 text-sm leading-5 text-brand">{doc.description}</Text>
      </View>
      {isPending ? (
        <Button label="Adjuntar documento" icon={Paperclip} variant="secondary" onPress={chooseSource} loading={busy} />
      ) : (
        <Text className="text-xs font-medium text-accent">
          {doc.status === 'submitted' ? 'Entregado ✓' : 'Eximido'}
        </Text>
      )}
    </View>
  )
}
