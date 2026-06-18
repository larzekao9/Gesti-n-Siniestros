// CU-35: clasificación de severidad de daño on-device (TFLite / MobileNetV2).
// Corre offline en el APK vía react-native-fast-tflite. El resultado
// { tipo, severidad, confianza } viaja en metadata.damage_classification al
// registrar la evidencia (mismo canal que el ocr_text de CU-34).
//
// Módulo NATIVO (fast-tflite): igual que ocr.ts, degradamos con gracia — si el
// nativo no está disponible (Expo Go) o algo falla, classifyDamage devuelve null
// y la evidencia se sube igual, sin clasificación. Regla F-A1: "no inventar".

import { manipulateAsync, SaveFormat } from 'expo-image-manipulator'
import { toByteArray } from 'base64-js'
import * as jpeg from 'jpeg-js'

import labels from '../../assets/models/damage_labels.json'

export interface DamageClassification {
  tipo: string
  severidad: string
  confianza: number
}

type TfliteLike = {
  run: (input: ArrayBuffer[]) => Promise<ArrayBuffer[]>
}

// require dinámico (no import estático) para que la ausencia del módulo nativo
// no tumbe el bundle en Expo Go.
let loadModel:
  | ((src: number, delegates: never[]) => Promise<TfliteLike>)
  | null = null
try {
  loadModel = require('react-native-fast-tflite').loadTensorflowModel
} catch {
  loadModel = null
}

const INPUT_SIZE: number = (labels as { input_size?: number }).input_size ?? 224
const CLASSES: string[] = (labels as { classes: string[] }).classes
const PRETTY: string[] = (labels as { pretty?: string[] }).pretty ?? CLASSES
// Umbral de confianza (debajo → no setear, F-A1 "no inventar"). Se subió de
// 0.6 a 0.75: con accuracy ~0.69, las predicciones flojas (apenas sobre 0.6)
// suelen ser erradas — mejor callar que mostrar una severidad equivocada. El
// consumo (web/backend) también filtra por 0.75, así que datos viejos por
// debajo quedan suprimidos sin rebuild.
const CONF_THRESHOLD = 0.75

// El modelo se carga una sola vez y se cachea entre fotos.
let modelPromise: Promise<TfliteLike> | null = null
function getModel(): Promise<TfliteLike> | null {
  if (!loadModel) return null
  if (!modelPromise) {
    modelPromise = loadModel(
      require('../../assets/models/damage_mobilenet.tflite'),
      []
    ).catch((e) => {
      modelPromise = null // permite reintentar en la próxima foto
      throw e
    })
  }
  return modelPromise
}

/** JPEG (base64) → Float32 [H*W*3] normalizado a [-1,1] (preprocess MobileNetV2). */
function toInputTensor(base64: string): Float32Array {
  const bytes = toByteArray(base64)
  const { data, width, height } = jpeg.decode(bytes, {
    useTArray: true,
    formatAsRGBA: true,
  })
  const out = new Float32Array(width * height * 3)
  let j = 0
  for (let i = 0; i < width * height; i++) {
    const p = i * 4 // RGBA → tomamos RGB, descartamos alpha
    out[j++] = data[p] / 127.5 - 1
    out[j++] = data[p + 1] / 127.5 - 1
    out[j++] = data[p + 2] / 127.5 - 1
  }
  return out
}

function argmax(arr: Float32Array): number {
  let best = 0
  for (let i = 1; i < arr.length; i++) {
    if (arr[i] > arr[best]) best = i
  }
  return best
}

/** Clasifica la severidad del daño de una foto. Devuelve null si el modelo no
 * está disponible, si la imagen no se puede procesar, o si la confianza es baja. */
export async function classifyDamage(
  uri: string
): Promise<DamageClassification | null> {
  try {
    const pending = getModel()
    if (!pending) return null
    const model = await pending

    const resized = await manipulateAsync(
      uri,
      [{ resize: { width: INPUT_SIZE, height: INPUT_SIZE } }],
      { base64: true, format: SaveFormat.JPEG, compress: 1 }
    )
    if (!resized.base64) return null

    const input = toInputTensor(resized.base64)
    // Un Float32Array nuevo siempre tiene un ArrayBuffer real (no SharedArrayBuffer).
    const outputs = await model.run([input.buffer as ArrayBuffer])
    const probs = new Float32Array(outputs[0])
    if (probs.length !== CLASSES.length) return null

    const idx = argmax(probs)
    const confianza = probs[idx]
    if (confianza < CONF_THRESHOLD) return null // F-A1

    return {
      tipo: 'daño_carroceria', // genérico por ahora (lo entrenado es la severidad)
      severidad: PRETTY[idx] ?? CLASSES[idx],
      confianza: Math.round(confianza * 1000) / 1000,
    }
  } catch {
    return null // degradación elegante: nunca bloquea la subida
  }
}
