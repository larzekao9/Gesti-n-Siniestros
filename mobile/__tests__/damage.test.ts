// CU-35: tests de la lógica de clasificación de severidad on-device.
// Se mockean los módulos nativos/pesados (fast-tflite, image-manipulator, jpeg)
// para testear la lógica pura: umbral F-A1, mapeo argmax→clase y degradación.

// Variables compartidas con los mocks (deben empezar con "mock" por el hoisting de jest).
let mockProbs: number[] = [0, 0, 0, 1]
let mockRunThrows = false
let mockBase64: string | undefined = 'ZmFrZQ=='

jest.mock('react-native-fast-tflite', () => ({
  loadTensorflowModel: jest.fn(async () => ({
    run: jest.fn(async () => {
      if (mockRunThrows) throw new Error('inference failed')
      return [new Float32Array(mockProbs).buffer]
    }),
  })),
}))

jest.mock('expo-image-manipulator', () => ({
  SaveFormat: { JPEG: 'jpeg' },
  manipulateAsync: jest.fn(async () => ({ base64: mockBase64 })),
}))

jest.mock('base64-js', () => ({
  toByteArray: jest.fn(() => new Uint8Array(2 * 2 * 4)),
}))

jest.mock('jpeg-js', () => ({
  decode: jest.fn(() => ({ width: 2, height: 2, data: new Uint8Array(2 * 2 * 4) })),
}))

// El modelo .tflite es un binario que en el celu maneja Metro; en jest no hay
// loader para esa extensión, así que lo mockeamos como un asset id cualquiera.
jest.mock('../assets/models/damage_mobilenet.tflite', () => 1, { virtual: true })

import { classifyDamage } from '@/lib/ml/damage'

beforeEach(() => {
  mockProbs = [0, 0, 0, 1]
  mockRunThrows = false
  mockBase64 = 'ZmFrZQ=='
})

describe('classifyDamage (CU-35)', () => {
  it('clasifica con confianza alta y mapea el índice del softmax a la clase', async () => {
    mockProbs = [0.02, 0.03, 0.05, 0.9] // argmax = 3 → severo
    const r = await classifyDamage('file://foto.jpg')
    expect(r).toEqual({ tipo: 'daño_carroceria', severidad: 'Severo', confianza: 0.9 })
  })

  it('mapea correctamente una clase intermedia (moderado)', async () => {
    mockProbs = [0.05, 0.1, 0.8, 0.05] // argmax = 2 → moderado
    const r = await classifyDamage('file://foto.jpg')
    expect(r?.severidad).toBe('Moderado')
    expect(r?.confianza).toBe(0.8)
  })

  it('F-A1: suprime la clasificación si la confianza es menor a 0.75 (no inventa)', async () => {
    mockProbs = [0.2, 0.64, 0.1, 0.06] // argmax = 1 (leve) con confianza 0.64 < 0.75
    const r = await classifyDamage('file://foto.jpg')
    expect(r).toBeNull()
  })

  it('acepta la clasificación justo en el umbral 0.75', async () => {
    mockProbs = [0.1, 0.1, 0.05, 0.75] // argmax = 3, confianza 0.75 = umbral
    const r = await classifyDamage('file://foto.jpg')
    expect(r?.severidad).toBe('Severo')
    expect(r?.confianza).toBe(0.75)
  })

  it('degradación elegante: si la inferencia falla, devuelve null (no rompe la subida)', async () => {
    mockRunThrows = true
    const r = await classifyDamage('file://foto.jpg')
    expect(r).toBeNull()
  })

  it('degradación elegante: si no se pudo obtener la imagen, devuelve null', async () => {
    mockBase64 = undefined
    const r = await classifyDamage('file://foto.jpg')
    expect(r).toBeNull()
  })
})
