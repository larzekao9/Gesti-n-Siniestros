// CU-34: OCR on-device de documentos (parte de tránsito, factura) con ML Kit.
// El texto extraído viaja en `metadata.ocr_text` al registrar la evidencia y lo
// consume el InconsistencyAnalysisService de la web (CU-32).
//
// Módulo NATIVO: requiere un dev/EAS build (no corre en Expo Go). Para no romper
// el flujo en Expo Go, degradamos con gracia: si el módulo nativo no está
// disponible, extractText devuelve '' y la evidencia se sube igual sin OCR.

let TextRecognition: { recognize: (uri: string) => Promise<{ text?: string }> } | null = null
try {
  // require (no import estático) para que la ausencia del nativo no tumbe el bundle.
  TextRecognition = require('@react-native-ml-kit/text-recognition').default
} catch {
  TextRecognition = null
}

/** Texto reconocido en la imagen, o '' si no hay texto / el OCR no está disponible. */
export async function extractText(uri: string): Promise<string> {
  if (!TextRecognition) return ''
  try {
    const result = await TextRecognition.recognize(uri)
    return (result?.text ?? '').trim()
  } catch {
    // F-A1: imagen sin texto reconocible o nativo ausente → sin OCR, no bloquea.
    return ''
  }
}
