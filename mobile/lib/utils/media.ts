// Captura de evidencias: cámara en vivo + galería, con manejo de permisos.
import * as ImagePicker from 'expo-image-picker'

import type { LocalAsset } from '../api/evidences'
import type { EvidenceType } from '@/types/evidence'

function inferType(mime: string): EvidenceType {
  if (mime.startsWith('video/')) return 'video'
  if (mime.startsWith('image/')) return 'photo'
  return 'other'
}

function toLocalAsset(asset: ImagePicker.ImagePickerAsset): LocalAsset {
  const mime = asset.mimeType ?? (asset.type === 'video' ? 'video/mp4' : 'image/jpeg')
  const fileName =
    asset.fileName ?? `evidencia-${Date.now()}.${mime.split('/')[1] ?? 'jpg'}`
  return {
    uri: asset.uri,
    fileName,
    mimeType: mime,
    fileSize: asset.fileSize ?? 0,
    type: inferType(mime),
  }
}

/** Abre la cámara para tomar una foto. Devuelve null si se cancela o se deniega. */
export async function captureFromCamera(): Promise<LocalAsset | null> {
  const perm = await ImagePicker.requestCameraPermissionsAsync()
  if (!perm.granted) {
    throw new Error('Necesitamos permiso de cámara para tomar la foto')
  }
  const result = await ImagePicker.launchCameraAsync({
    mediaTypes: ['images'],
    quality: 0.7,
    exif: false,
  })
  if (result.canceled || !result.assets?.length) return null
  return toLocalAsset(result.assets[0])
}

/** Abre la galería para elegir imágenes/videos (múltiple). */
export async function pickFromGallery(): Promise<LocalAsset[]> {
  const perm = await ImagePicker.requestMediaLibraryPermissionsAsync()
  if (!perm.granted) {
    throw new Error('Necesitamos permiso para acceder a tus fotos')
  }
  const result = await ImagePicker.launchImageLibraryAsync({
    mediaTypes: ['images', 'videos'],
    quality: 0.7,
    allowsMultipleSelection: true,
    selectionLimit: 6,
  })
  if (result.canceled || !result.assets?.length) return []
  return result.assets.map(toLocalAsset)
}
