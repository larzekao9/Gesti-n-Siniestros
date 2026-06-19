// CU-36: guía de calidad de evidencia on-device (gate previo a subir).
// Antes de subir una foto, se corren 3 checks (spec CU-36 / ADR-012):
//   - blur:   varianza del Laplaciano (heurística pura, sin ML)
//   - brillo: luminancia media (heurística pura, sin ML)
//   - "¿hay un vehículo?": MobileNet COMPARTIDO con CU-35 (mismo modelo, una sola
//     carga) — se aproxima con la confianza máxima del softmax.
//
// Es ADVISORY (F-A1): si la foto no pasa, se AVISA pero NO se bloquea — el
// asegurado puede subir igual. Ante cualquier error, se trata como "ok" para
// no trabar la subida nunca.
//
// Nota honesta: el modelo de CU-35 es un clasificador de SEVERIDAD (4 clases de
// auto), no un detector de vehículo. El check "¿hay vehículo?" se aproxima con
// la confianza del softmax (baja → la imagen no se parece a un auto conocido);
// es una señal débil, por eso el umbral es laxo para no molestar de más.

import { manipulateAsync, SaveFormat } from 'expo-image-manipulator'
import { toByteArray } from 'base64-js'
import * as jpeg from 'jpeg-js'

import { inferProbs } from './damage'

// Tamaño chico: el análisis de píxeles (blur/brillo) es instantáneo así.
const QUALITY_SIZE = 128
// Umbrales heurísticos (ajustables). Sobre luma 0..255.
const BLUR_MIN_VARIANCE = 100 // varianza de Laplaciano por debajo → borrosa
const DARK_MIN_BRIGHTNESS = 40 // luminancia media por debajo → muy oscura
const BRIGHT_MAX_BRIGHTNESS = 235 // por encima → quemada (sobreexpuesta)
const VEHICLE_MIN_CONF = 0.4 // confianza máx del MobileNet por debajo → no se ve claro el vehículo

export type QualityIssue = 'blurry' | 'dark' | 'overexposed' | 'no_vehicle'

export interface QualityResult {
  ok: boolean
  issues: QualityIssue[]
  /** Mensaje listo para mostrar al usuario (vacío si está todo bien). */
  message: string
}

const MESSAGES: Record<QualityIssue, string> = {
  blurry: 'La foto se ve borrosa',
  dark: 'La foto está muy oscura',
  overexposed: 'La foto está muy quemada por la luz',
  no_vehicle: 'No se distingue bien el vehículo',
}

/** Luminancia media (0..255) — BT.601. */
export function meanBrightness(gray: number[]): number {
  if (gray.length === 0) return 0
  let sum = 0
  for (let i = 0; i < gray.length; i++) sum += gray[i]
  return sum / gray.length
}

/** Varianza del Laplaciano 3x3. Valores bajos → imagen borrosa/desenfocada. */
export function laplacianVariance(gray: number[], width: number, height: number): number {
  const lap: number[] = []
  for (let y = 1; y < height - 1; y++) {
    for (let x = 1; x < width - 1; x++) {
      const i = y * width + x
      lap.push(4 * gray[i] - gray[i - 1] - gray[i + 1] - gray[i - width] - gray[i + width])
    }
  }
  if (lap.length === 0) return 0
  let mean = 0
  for (const v of lap) mean += v
  mean /= lap.length
  let varSum = 0
  for (const v of lap) varSum += (v - mean) * (v - mean)
  return varSum / lap.length
}

/** Decodifica la imagen a una matriz de grises (0..255) en tamaño chico. */
async function toGray(
  uri: string
): Promise<{ gray: number[]; width: number; height: number } | null> {
  const resized = await manipulateAsync(uri, [{ resize: { width: QUALITY_SIZE } }], {
    base64: true,
    format: SaveFormat.JPEG,
    compress: 1,
  })
  if (!resized.base64) return null
  const { data, width, height } = jpeg.decode(toByteArray(resized.base64), {
    useTArray: true,
    formatAsRGBA: true,
  })
  const gray = new Array<number>(width * height)
  for (let i = 0; i < width * height; i++) {
    const p = i * 4
    gray[i] = 0.299 * data[p] + 0.587 * data[p + 1] + 0.114 * data[p + 2]
  }
  return { gray, width, height }
}

/** Gate de calidad de la foto (CU-36). Advisory: nunca bloquea (F-A1). */
export async function checkPhotoQuality(uri: string): Promise<QualityResult> {
  const issues: QualityIssue[] = []
  try {
    const g = await toGray(uri)
    if (g) {
      const brightness = meanBrightness(g.gray)
      if (brightness < DARK_MIN_BRIGHTNESS) issues.push('dark')
      else if (brightness > BRIGHT_MAX_BRIGHTNESS) issues.push('overexposed')

      if (laplacianVariance(g.gray, g.width, g.height) < BLUR_MIN_VARIANCE) {
        issues.push('blurry')
      }
    }

    // "¿hay un vehículo?" con el MobileNet compartido (CU-35). Si el nativo no
    // está disponible (Expo Go), inferProbs devuelve null y se omite el check.
    const probs = await inferProbs(uri)
    if (probs) {
      let maxP = 0
      for (let i = 0; i < probs.length; i++) if (probs[i] > maxP) maxP = probs[i]
      if (maxP < VEHICLE_MIN_CONF) issues.push('no_vehicle')
    }
  } catch {
    // Ante cualquier error no trabamos la subida: tratamos como ok (F-A1).
    return { ok: true, issues: [], message: '' }
  }

  const message = issues.length
    ? `${issues.map((i) => MESSAGES[i]).join('. ')}. ¿Querés tomar otra?`
    : ''
  return { ok: issues.length === 0, issues, message }
}
