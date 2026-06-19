// CU-36: tests del gate de calidad de evidencia. Se testean las heurísticas
// puras (brillo, blur) directamente y el gate completo con mocks de los módulos
// pesados (image-manipulator, jpeg) y del modelo compartido (inferProbs).

let mockPixels: Uint8Array = new Uint8Array(0)
let mockW = 4
let mockH = 4
let mockProbs: number[] | null = [0.9, 0.03, 0.04, 0.03]
let mockThrow = false

jest.mock('expo-image-manipulator', () => ({
  SaveFormat: { JPEG: 'jpeg' },
  manipulateAsync: jest.fn(async () => {
    if (mockThrow) throw new Error('manip failed')
    return { base64: 'x' }
  }),
}))

jest.mock('base64-js', () => ({ toByteArray: jest.fn(() => new Uint8Array(0)) }))

jest.mock('jpeg-js', () => ({
  decode: jest.fn(() => ({ width: mockW, height: mockH, data: mockPixels })),
}))

// El modelo es el COMPARTIDO con CU-35; lo mockeamos vía inferProbs.
jest.mock('@/lib/ml/damage', () => ({
  inferProbs: jest.fn(async () => (mockProbs ? new Float32Array(mockProbs) : null)),
}))

import { checkPhotoQuality, meanBrightness, laplacianVariance } from '@/lib/ml/quality'

function uniformRGBA(value: number, w: number, h: number): Uint8Array {
  const a = new Uint8Array(w * h * 4)
  for (let i = 0; i < w * h; i++) {
    a[i * 4] = value
    a[i * 4 + 1] = value
    a[i * 4 + 2] = value
    a[i * 4 + 3] = 255
  }
  return a
}

function checkerRGBA(w: number, h: number): Uint8Array {
  const a = new Uint8Array(w * h * 4)
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const i = y * w + x
      const v = (x + y) % 2 === 0 ? 255 : 0
      a[i * 4] = v
      a[i * 4 + 1] = v
      a[i * 4 + 2] = v
      a[i * 4 + 3] = 255
    }
  }
  return a
}

beforeEach(() => {
  mockW = 4
  mockH = 4
  mockProbs = [0.9, 0.03, 0.04, 0.03]
  mockThrow = false
  mockPixels = checkerRGBA(4, 4) // imagen "buena" por defecto (nítida, brillo medio)
})

describe('heurísticas puras', () => {
  it('meanBrightness promedia la luminancia', () => {
    expect(meanBrightness([0, 0])).toBe(0)
    expect(meanBrightness([100, 200])).toBe(150)
  })

  it('laplacianVariance ~0 en imagen plana (borrosa)', () => {
    const flat = new Array(16).fill(100)
    expect(laplacianVariance(flat, 4, 4)).toBe(0)
  })

  it('laplacianVariance alta en imagen con bordes nítidos', () => {
    const checker = new Array(16)
    for (let y = 0; y < 4; y++) for (let x = 0; x < 4; x++) checker[y * 4 + x] = (x + y) % 2 === 0 ? 255 : 0
    expect(laplacianVariance(checker, 4, 4)).toBeGreaterThan(100)
  })
})

describe('checkPhotoQuality (CU-36)', () => {
  it('una foto nítida, con brillo y vehículo reconocible pasa el gate', async () => {
    const r = await checkPhotoQuality('file://ok.jpg')
    expect(r.ok).toBe(true)
    expect(r.issues).toEqual([])
  })

  it('detecta foto muy oscura (y borrosa por plana)', async () => {
    mockPixels = uniformRGBA(10, 4, 4)
    const r = await checkPhotoQuality('file://dark.jpg')
    expect(r.ok).toBe(false)
    expect(r.issues).toContain('dark')
    expect(r.issues).toContain('blurry')
  })

  it('detecta cuando no se distingue el vehículo (confianza baja del modelo)', async () => {
    mockProbs = [0.3, 0.3, 0.2, 0.2] // maxP 0.3 < umbral
    const r = await checkPhotoQuality('file://novehicle.jpg')
    expect(r.issues).toContain('no_vehicle')
  })

  it('omite el check de vehículo si el modelo no está disponible (degradación)', async () => {
    mockProbs = null // inferProbs → null (Expo Go / sin nativo)
    const r = await checkPhotoQuality('file://ok.jpg')
    expect(r.issues).not.toContain('no_vehicle')
    expect(r.ok).toBe(true)
  })

  it('nunca bloquea: ante un error trata la foto como ok (F-A1)', async () => {
    mockThrow = true
    const r = await checkPhotoQuality('file://err.jpg')
    expect(r.ok).toBe(true)
    expect(r.issues).toEqual([])
  })
})
