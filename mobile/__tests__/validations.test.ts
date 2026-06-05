import {
  forgotPasswordSchema,
  insuredLoginSchema,
  registerWithTokenSchema,
} from '@/lib/validations/auth'
import { accidentStepSchema, vehicleStepSchema } from '@/lib/validations/claim-request'

describe('insuredLoginSchema', () => {
  it('acepta credenciales válidas', () => {
    const r = insuredLoginSchema.safeParse({
      tenant_slug: 'aseguradora-a',
      email: 'juan@mail.com',
      password: 'secret',
    })
    expect(r.success).toBe(true)
  })

  it('rechaza tenant slug con mayúsculas', () => {
    const r = insuredLoginSchema.safeParse({
      tenant_slug: 'Aseguradora_A',
      email: 'juan@mail.com',
      password: 'secret',
    })
    expect(r.success).toBe(false)
  })

  it('rechaza email inválido', () => {
    const r = insuredLoginSchema.safeParse({
      tenant_slug: 'a',
      email: 'no-es-email',
      password: 'x',
    })
    expect(r.success).toBe(false)
  })
})

describe('registerWithTokenSchema', () => {
  it('rechaza si las contraseñas no coinciden', () => {
    const r = registerWithTokenSchema.safeParse({
      activation_token: '1234567890abc',
      password: 'Password1',
      confirm_password: 'Password2',
    })
    expect(r.success).toBe(false)
  })

  it('rechaza contraseña sin mayúscula o número', () => {
    const r = registerWithTokenSchema.safeParse({
      activation_token: '1234567890abc',
      password: 'password',
      confirm_password: 'password',
    })
    expect(r.success).toBe(false)
  })

  it('acepta un registro válido', () => {
    const r = registerWithTokenSchema.safeParse({
      activation_token: '1234567890abc',
      password: 'Password1',
      confirm_password: 'Password1',
    })
    expect(r.success).toBe(true)
  })
})

describe('forgotPasswordSchema', () => {
  it('requiere tenant y email', () => {
    expect(forgotPasswordSchema.safeParse({ tenant_slug: '', email: '' }).success).toBe(
      false
    )
  })
})

describe('accidentStepSchema', () => {
  it('rechaza fecha mal formada', () => {
    const r = accidentStepSchema.safeParse({
      accident_date: '03-06-2026',
      accident_location: 'Av. Siempreviva 742',
      accident_description: 'Choque en la esquina contra un poste',
    })
    expect(r.success).toBe(false)
  })

  it('rechaza descripción demasiado corta', () => {
    const r = accidentStepSchema.safeParse({
      accident_date: '2026-06-03',
      accident_location: 'Av. Siempreviva 742',
      accident_description: 'corto',
    })
    expect(r.success).toBe(false)
  })

  it('acepta datos mínimos válidos', () => {
    const r = accidentStepSchema.safeParse({
      accident_date: '2026-06-03',
      accident_location: 'Av. Siempreviva 742',
      accident_description: 'Choque leve en la intersección, sin heridos',
    })
    expect(r.success).toBe(true)
  })
})

describe('vehicleStepSchema', () => {
  it('exige vehículo y póliza', () => {
    expect(vehicleStepSchema.safeParse({ policy_id: '', vehicle_id: '' }).success).toBe(
      false
    )
    expect(
      vehicleStepSchema.safeParse({ policy_id: 'p1', vehicle_id: 'v1' }).success
    ).toBe(true)
  })
})
