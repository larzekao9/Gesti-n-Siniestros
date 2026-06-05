import { Image, Pressable, Text, View } from 'react-native'
import { FileText, Video, X } from 'lucide-react-native'

import { colors } from '@/lib/theme'

interface EvidenceThumbProps {
  uri: string
  mimeType: string
  onRemove?: () => void
  uploading?: boolean
}

// Miniatura de evidencia capturada (antes de subir) o ya subida.
export function EvidenceThumb({ uri, mimeType, onRemove, uploading }: EvidenceThumbProps) {
  const isImage = mimeType.startsWith('image/')
  const isVideo = mimeType.startsWith('video/')
  return (
    <View className="h-24 w-24 overflow-hidden rounded-xl border border-line bg-background">
      {isImage ? (
        <Image source={{ uri }} className="h-full w-full" resizeMode="cover" />
      ) : (
        <View className="h-full w-full items-center justify-center">
          {isVideo ? (
            <Video size={26} color={colors.muted} />
          ) : (
            <FileText size={26} color={colors.muted} />
          )}
        </View>
      )}
      {uploading ? (
        <View className="absolute inset-0 items-center justify-center bg-black/40">
          <Text className="text-[10px] font-medium text-white">Subiendo…</Text>
        </View>
      ) : null}
      {onRemove ? (
        <Pressable
          onPress={onRemove}
          hitSlop={8}
          accessibilityLabel="Quitar evidencia"
          className="absolute right-1 top-1 h-6 w-6 items-center justify-center rounded-full bg-black/60"
        >
          <X size={14} color={colors.white} />
        </Pressable>
      ) : null}
    </View>
  )
}
