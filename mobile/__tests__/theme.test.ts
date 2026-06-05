import { statusStyle } from '@/lib/theme'
import { formatDate, todayISODate } from '@/lib/utils/format'

describe('statusStyle', () => {
  it('mapea estados conocidos a una etiqueta legible', () => {
    expect(statusStyle('submitted').label).toBe('Enviada')
    expect(statusStyle('approved').label).toBe('Aprobado')
    expect(statusStyle('rejected_at_intake').label).toBe('Rechazada')
  })

  it('devuelve un fallback para estados desconocidos', () => {
    const s = statusStyle('unknown_state')
    expect(s.label).toBe('unknown_state')
    expect(s.bg).toBeTruthy()
  })
})

describe('format', () => {
  it('formatea fechas ISO en español', () => {
    expect(formatDate('2026-06-03')).toContain('jun')
    expect(formatDate('2026-06-03')).toContain('2026')
  })

  it('devuelve guion para nulos', () => {
    expect(formatDate(null)).toBe('—')
  })

  it('todayISODate devuelve formato AAAA-MM-DD', () => {
    expect(todayISODate()).toMatch(/^\d{4}-\d{2}-\d{2}$/)
  })
})
