/**
 * Tests for RegisterForm component.
 *
 * Covers:
 *  - Renders all four fields with visible labels
 *  - Validation: name too short, invalid email, weak password, bad slug
 *  - Successful register → setAuth + router.push('/mfa/setup')
 *  - 409 conflict → toast "Ya existe una cuenta con ese correo"
 *  - Generic API error → toast with detail message
 *  - Loading state during submit
 *  - Link back to /login
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { render } from '../../helpers/test-utils'
import { RegisterForm } from '@/components/auth/RegisterForm'
import * as authApiModule from '@/lib/api/auth'
import { useAuthStore } from '@/lib/stores/authStore'
import { mockTokenResponse } from '../../helpers/mocks'

// ------------------------------------------------------------------
// Module mocks
// ------------------------------------------------------------------
const mockPush = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
}))

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
  },
}))

vi.mock('@/lib/api/auth', () => ({
  authApi: {
    register: vi.fn(),
  },
}))

// Mock axios isAxiosError so our hand-crafted error objects are recognized
vi.mock('axios', async (importOriginal) => {
  const actual = await importOriginal<typeof import('axios')>()
  return {
    ...actual,
    isAxiosError: (err: unknown): err is import('axios').AxiosError =>
      (err as { isAxiosError?: boolean })?.isAxiosError === true,
  }
})

// ------------------------------------------------------------------
// Helpers
// ------------------------------------------------------------------
const VALID_VALUES = {
  full_name: 'María García',
  email: 'maria@aseguradora.com',
  password: 'Segura123',
  tenant_slug: 'mi-aseguradora',
}

async function fillForm(
  user: ReturnType<typeof userEvent.setup>,
  overrides: Partial<typeof VALID_VALUES> = {}
) {
  const values = { ...VALID_VALUES, ...overrides }
  await user.type(screen.getByLabelText(/nombre completo/i), values.full_name)
  await user.tab() // blur → validate
  await user.type(screen.getByLabelText(/correo electrónico/i), values.email)
  await user.tab() // blur → validate
  // Use exact label to avoid ambiguity with toggle button aria-label
  await user.type(screen.getByLabelText('Contraseña'), values.password)
  await user.tab() // blur → validate
  await user.type(
    screen.getByLabelText(/identificador de organización/i),
    values.tenant_slug
  )
  await user.tab() // blur → validate — isValid becomes true
}

// ------------------------------------------------------------------
// Tests
// ------------------------------------------------------------------
describe('RegisterForm', () => {
  const registerMock = vi.mocked(authApiModule.authApi.register)

  beforeEach(() => {
    vi.clearAllMocks()
    useAuthStore.setState({ user: null, accessToken: null, isLoading: false })
  })

  // ----------------------------------------------------------------
  // Rendering
  // ----------------------------------------------------------------
  it('renderiza los cuatro campos con etiquetas visibles', () => {
    render(<RegisterForm />)

    expect(screen.getByLabelText(/nombre completo/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/correo electrónico/i)).toBeInTheDocument()
    // Use exact label text to avoid matching toggle button aria-label
    expect(screen.getByLabelText('Contraseña')).toBeInTheDocument()
    expect(
      screen.getByLabelText(/identificador de organización/i)
    ).toBeInTheDocument()
  })

  it('muestra el botón "Crear cuenta"', () => {
    render(<RegisterForm />)
    expect(
      screen.getByRole('button', { name: /crear cuenta/i })
    ).toBeInTheDocument()
  })

  it('el enlace "Iniciar sesión" apunta a /login', () => {
    render(<RegisterForm />)
    expect(
      screen.getByRole('link', { name: /iniciar sesión/i })
    ).toHaveAttribute('href', '/login')
  })

  // ----------------------------------------------------------------
  // Validation
  // ----------------------------------------------------------------
  it('muestra error cuando el nombre es demasiado corto', async () => {
    const user = userEvent.setup()
    render(<RegisterForm />)

    await user.type(screen.getByLabelText(/nombre completo/i), 'A')
    await user.tab()

    const alert = await screen.findByRole('alert')
    // Zod message: "El nombre debe tener al menos 2 caracteres"
    expect(alert).toHaveTextContent(/al menos 2 caracteres/i)
  })

  it('muestra error de email inválido', async () => {
    const user = userEvent.setup()
    render(<RegisterForm />)

    await user.type(screen.getByLabelText(/correo electrónico/i), 'not-email')
    await user.tab()

    expect(await screen.findByRole('alert')).toHaveTextContent(/email inválido/i)
  })

  it('muestra error cuando la contraseña es demasiado corta', async () => {
    const user = userEvent.setup()
    render(<RegisterForm />)

    await user.type(screen.getByLabelText('Contraseña'), 'corta')
    await user.tab()

    expect(await screen.findByRole('alert')).toHaveTextContent(
      /al menos 8 caracteres/i
    )
  })

  it('muestra error cuando la contraseña no tiene mayúsculas', async () => {
    const user = userEvent.setup()
    render(<RegisterForm />)

    await user.type(screen.getByLabelText('Contraseña'), 'sinmayuscula1')
    await user.tab()

    expect(await screen.findByRole('alert')).toHaveTextContent(/mayúscula/i)
  })

  it('muestra error cuando el tenant_slug tiene caracteres inválidos', async () => {
    const user = userEvent.setup()
    render(<RegisterForm />)

    await user.type(
      screen.getByLabelText(/identificador de organización/i),
      'MiEmpresa!'
    )
    await user.tab()

    expect(await screen.findByRole('alert')).toHaveTextContent(
      /minúsculas.*números.*guiones/i
    )
  })

  // ----------------------------------------------------------------
  // Happy path
  // ----------------------------------------------------------------
  it('registro exitoso llama setAuth y redirige a /mfa/setup', async () => {
    const tokenResponse = mockTokenResponse()
    registerMock.mockResolvedValueOnce(tokenResponse)

    const user = userEvent.setup()
    render(<RegisterForm />)
    await fillForm(user)
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /crear cuenta/i })).not.toBeDisabled()
    })
    await user.click(screen.getByRole('button', { name: /crear cuenta/i }))

    await waitFor(() => {
      expect(registerMock).toHaveBeenCalledWith(VALID_VALUES)
    })

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/mfa/setup')
    })

    const { user: storedUser } = useAuthStore.getState()
    expect(storedUser?.email).toBe(tokenResponse.user.email)
  })

  // ----------------------------------------------------------------
  // Error: 409 conflict
  // ----------------------------------------------------------------
  it('error 409 muestra toast de email ya registrado', async () => {
    const { toast } = await import('sonner')
    const axiosError = Object.assign(new Error('Conflict'), {
      isAxiosError: true,
      response: { status: 409, data: { detail: 'Email already exists' } },
    })
    registerMock.mockRejectedValueOnce(axiosError)

    const user = userEvent.setup()
    render(<RegisterForm />)
    await fillForm(user)
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /crear cuenta/i })).not.toBeDisabled()
    })
    await user.click(screen.getByRole('button', { name: /crear cuenta/i }))

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        'Ya existe una cuenta con ese correo electrónico.'
      )
    })
    expect(mockPush).not.toHaveBeenCalled()
  })

  // ----------------------------------------------------------------
  // Error: API with detail
  // ----------------------------------------------------------------
  it('error de API con detail lo muestra en el toast', async () => {
    const { toast } = await import('sonner')
    const axiosError = Object.assign(new Error('Bad Request'), {
      isAxiosError: true,
      response: {
        status: 422,
        data: { detail: 'El tenant ya existe' },
      },
    })
    registerMock.mockRejectedValueOnce(axiosError)

    const user = userEvent.setup()
    render(<RegisterForm />)
    await fillForm(user)
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /crear cuenta/i })).not.toBeDisabled()
    })
    await user.click(screen.getByRole('button', { name: /crear cuenta/i }))

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('El tenant ya existe')
    })
  })

  // ----------------------------------------------------------------
  // Loading state
  // ----------------------------------------------------------------
  it('el botón muestra "Creando cuenta..." mientras se envía', async () => {
    registerMock.mockImplementationOnce(
      () => new Promise<never>(() => undefined)
    )

    const user = userEvent.setup()
    render(<RegisterForm />)
    await fillForm(user)
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /crear cuenta/i })).not.toBeDisabled()
    })
    await user.click(screen.getByRole('button', { name: /crear cuenta/i }))

    const btn = await screen.findByRole('button', { name: /creando cuenta/i })
    expect(btn).toBeDisabled()
  })
})
