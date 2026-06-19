/**
 * Tests for Zod validation schemas.
 *
 * Covers every rule in loginSchema, registerSchema and mfaVerifySchema.
 */
import { describe, it, expect } from 'vitest'
import {
  loginSchema,
  registerSchema,
  mfaVerifySchema,
} from '@/lib/validations/auth'

// ------------------------------------------------------------------
// loginSchema
// ------------------------------------------------------------------
describe('loginSchema', () => {
  // tenant_slug es requerido por loginSchema (multi-tenant). Sin él, el primer
  // issue era el de tenant faltante y los asserts apuntaban al campo equivocado.
  const valid = { tenant_slug: 'mi-empresa', email: 'user@empresa.com', password: 'secret123', mfa_code: '' }

  it('acepta valores válidos', () => {
    expect(loginSchema.safeParse(valid).success).toBe(true)
  })

  it('rechaza email inválido', () => {
    const result = loginSchema.safeParse({ ...valid, email: 'not-email' })
    expect(result.success).toBe(false)
    if (!result.success) {
      expect(result.error.issues[0].message).toMatch(/email inválido/i)
    }
  })

  it('rechaza contraseña vacía', () => {
    const result = loginSchema.safeParse({ ...valid, password: '' })
    expect(result.success).toBe(false)
    if (!result.success) {
      expect(result.error.issues[0].message).toMatch(/contraseña.*requerida|requerido/i)
    }
  })

  it('acepta mfa_code de 6 dígitos', () => {
    expect(loginSchema.safeParse({ ...valid, mfa_code: '123456' }).success).toBe(true)
  })

  it('acepta mfa_code vacío (campo opcional)', () => {
    expect(loginSchema.safeParse({ ...valid, mfa_code: '' }).success).toBe(true)
  })

  it('rechaza mfa_code con longitud incorrecta', () => {
    const result = loginSchema.safeParse({ ...valid, mfa_code: '12345' })
    expect(result.success).toBe(false)
  })
})

// ------------------------------------------------------------------
// registerSchema
// ------------------------------------------------------------------
describe('registerSchema', () => {
  const valid = {
    full_name: 'María García',
    email: 'maria@empresa.com',
    password: 'Segura123',
    tenant_slug: 'mi-empresa',
  }

  it('acepta valores válidos', () => {
    expect(registerSchema.safeParse(valid).success).toBe(true)
  })

  it('rechaza nombre con menos de 2 caracteres', () => {
    const result = registerSchema.safeParse({ ...valid, full_name: 'A' })
    expect(result.success).toBe(false)
    if (!result.success) {
      expect(result.error.issues[0].message).toMatch(/al menos 2 caracteres/i)
    }
  })

  it('rechaza nombre con más de 100 caracteres', () => {
    const result = registerSchema.safeParse({
      ...valid,
      full_name: 'A'.repeat(101),
    })
    expect(result.success).toBe(false)
  })

  it('rechaza email inválido', () => {
    const result = registerSchema.safeParse({ ...valid, email: 'bad' })
    expect(result.success).toBe(false)
    if (!result.success) {
      expect(result.error.issues[0].message).toMatch(/email inválido/i)
    }
  })

  it('rechaza contraseña con menos de 8 caracteres', () => {
    const result = registerSchema.safeParse({ ...valid, password: 'Abc1' })
    expect(result.success).toBe(false)
    if (!result.success) {
      expect(result.error.issues[0].message).toMatch(/al menos 8 caracteres/i)
    }
  })

  it('rechaza contraseña sin mayúsculas', () => {
    const result = registerSchema.safeParse({ ...valid, password: 'sinmayuscula1' })
    expect(result.success).toBe(false)
    if (!result.success) {
      expect(result.error.issues[0].message).toMatch(/mayúscula/i)
    }
  })

  it('rechaza contraseña sin números', () => {
    const result = registerSchema.safeParse({ ...valid, password: 'SinNumeroAqui' })
    expect(result.success).toBe(false)
    if (!result.success) {
      expect(result.error.issues[0].message).toMatch(/número/i)
    }
  })

  it('rechaza tenant_slug con caracteres inválidos (mayúsculas)', () => {
    const result = registerSchema.safeParse({ ...valid, tenant_slug: 'MiEmpresa' })
    expect(result.success).toBe(false)
  })

  it('rechaza tenant_slug con espacios', () => {
    const result = registerSchema.safeParse({ ...valid, tenant_slug: 'mi empresa' })
    expect(result.success).toBe(false)
  })

  it('rechaza tenant_slug vacío', () => {
    const result = registerSchema.safeParse({ ...valid, tenant_slug: '' })
    expect(result.success).toBe(false)
    if (!result.success) {
      expect(result.error.issues[0].message).toMatch(/requerido/i)
    }
  })

  it('acepta tenant_slug con guiones y números', () => {
    expect(
      registerSchema.safeParse({ ...valid, tenant_slug: 'empresa-2024' }).success
    ).toBe(true)
  })
})

// ------------------------------------------------------------------
// mfaVerifySchema
// ------------------------------------------------------------------
describe('mfaVerifySchema', () => {
  it('acepta código de exactamente 6 dígitos', () => {
    expect(mfaVerifySchema.safeParse({ code: '123456' }).success).toBe(true)
  })

  it('rechaza código con menos de 6 dígitos', () => {
    const result = mfaVerifySchema.safeParse({ code: '12345' })
    expect(result.success).toBe(false)
    if (!result.success) {
      expect(result.error.issues[0].message).toMatch(/exactamente 6 dígitos/i)
    }
  })

  it('rechaza código con más de 6 dígitos', () => {
    const result = mfaVerifySchema.safeParse({ code: '1234567' })
    expect(result.success).toBe(false)
  })

  it('rechaza código con letras', () => {
    const result = mfaVerifySchema.safeParse({ code: '12a456' })
    expect(result.success).toBe(false)
    if (!result.success) {
      expect(result.error.issues[0].message).toMatch(/dígitos/i)
    }
  })

  it('rechaza código vacío', () => {
    const result = mfaVerifySchema.safeParse({ code: '' })
    expect(result.success).toBe(false)
  })
})
