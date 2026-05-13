/**
 * Tests for LoginForm component.
 *
 * Covers:
 *  - Renders all required fields and labels
 *  - Inline validation errors (empty password, invalid email)
 *  - Password visibility toggle
 *  - Successful login → setAuth called + router.push('/dashboard')
 *  - 401 → toast error "Email o contraseña incorrectos"
 *  - 403 + MFA detail → MFA code field appears
 *  - Network error → generic toast error
 *  - Submit button disabled while submitting
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { render } from '../../helpers/test-utils'
import { LoginForm } from '@/components/auth/LoginForm'
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
    login: vi.fn(),
  },
}))

// Mock isAxiosError so our hand-crafted error objects are recognized
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

/**
 * Fill in email + password, blur both fields so onBlur validation fires
 * and isValid becomes true, then click submit.
 */
const fillAndSubmit = async (
  user: ReturnType<typeof userEvent.setup>,
  email = 'test@empresa.com',
  password = 'Passw0rd!'
) => {
  const emailInput = screen.getByLabelText(/correo electrónico/i)
  const passwordInput = screen.getByLabelText('Contraseña')

  await user.type(emailInput, email)
  await user.tab() // blur email → triggers validation
  await user.type(passwordInput, password)
  await user.tab() // blur password → triggers validation + isValid becomes true

  // Wait for the button to become enabled before clicking
  await waitFor(() => {
    expect(screen.getByRole('button', { name: /iniciar sesión/i })).not.toBeDisabled()
  })
  await user.click(screen.getByRole('button', { name: /iniciar sesión/i }))
}

// ------------------------------------------------------------------
// Tests
// ------------------------------------------------------------------
describe('LoginForm', () => {
  const loginMock = vi.mocked(authApiModule.authApi.login)

  beforeEach(() => {
    vi.clearAllMocks()
    useAuthStore.setState({ user: null, accessToken: null, isLoading: false })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // ----------------------------------------------------------------
  // Rendering
  // ----------------------------------------------------------------
  it('renderiza el formulario con todos los campos requeridos', () => {
    render(<LoginForm />)

    expect(screen.getByLabelText(/correo electrónico/i)).toBeInTheDocument()
    // Exact match to avoid confusion with the toggle button aria-label
    expect(screen.getByLabelText('Contraseña')).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /iniciar sesión/i })
    ).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /registrarse/i })).toBeInTheDocument()
  })

  it('el campo de contraseña es de tipo password por defecto', () => {
    render(<LoginForm />)
    expect(screen.getByLabelText('Contraseña')).toHaveAttribute('type', 'password')
  })

  // ----------------------------------------------------------------
  // Validation — triggered on blur
  // ----------------------------------------------------------------
  it('muestra error de email inválido al perder el foco', async () => {
    const user = userEvent.setup()
    render(<LoginForm />)

    const emailInput = screen.getByLabelText(/correo electrónico/i)
    await user.type(emailInput, 'no-es-email')
    await user.tab()

    expect(await screen.findByRole('alert')).toHaveTextContent(/email inválido/i)
  })

  it('muestra error de contraseña requerida al hacer blur con el campo vacío', async () => {
    const user = userEvent.setup()
    render(<LoginForm />)

    // Click the password field then immediately tab away without typing
    await user.click(screen.getByLabelText('Contraseña'))
    await user.tab()

    expect(await screen.findByRole('alert')).toHaveTextContent(/requerida/i)
  })

  // ----------------------------------------------------------------
  // Password visibility toggle
  // ----------------------------------------------------------------
  it('el toggle muestra y oculta la contraseña', async () => {
    const user = userEvent.setup()
    render(<LoginForm />)

    const passwordInput = screen.getByLabelText('Contraseña')
    const toggleBtn = screen.getByRole('button', { name: /mostrar contraseña/i })

    expect(passwordInput).toHaveAttribute('type', 'password')

    await user.click(toggleBtn)
    expect(passwordInput).toHaveAttribute('type', 'text')

    await user.click(screen.getByRole('button', { name: /ocultar contraseña/i }))
    expect(passwordInput).toHaveAttribute('type', 'password')
  })

  // ----------------------------------------------------------------
  // Happy path
  // ----------------------------------------------------------------
  it('en login exitoso llama setAuth y redirige a /dashboard', async () => {
    const tokenResponse = mockTokenResponse()
    loginMock.mockResolvedValueOnce(tokenResponse)

    const user = userEvent.setup()
    render(<LoginForm />)
    await fillAndSubmit(user)

    await waitFor(() => {
      expect(loginMock).toHaveBeenCalledWith({
        email: 'test@empresa.com',
        password: 'Passw0rd!',
        mfa_code: undefined,
      })
    })

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/dashboard')
    })

    const { user: storedUser, accessToken } = useAuthStore.getState()
    expect(storedUser?.email).toBe(tokenResponse.user.email)
    expect(accessToken).toBe(tokenResponse.access_token)
  })

  // ----------------------------------------------------------------
  // Error: 401
  // ----------------------------------------------------------------
  it('error 401 muestra toast "Email o contraseña incorrectos"', async () => {
    const { toast } = await import('sonner')
    const axiosError = Object.assign(new Error('Unauthorized'), {
      isAxiosError: true,
      response: { status: 401, data: { detail: 'Invalid credentials' } },
    })
    loginMock.mockRejectedValueOnce(axiosError)

    const user = userEvent.setup()
    render(<LoginForm />)
    await fillAndSubmit(user)

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Email o contraseña incorrectos')
    })
    expect(mockPush).not.toHaveBeenCalled()
  })

  // ----------------------------------------------------------------
  // Error: 403 + MFA required
  // ----------------------------------------------------------------
  it('error 403 con detail MFA muestra el campo de código MFA', async () => {
    const axiosError = Object.assign(new Error('Forbidden'), {
      isAxiosError: true,
      response: {
        status: 403,
        data: { detail: 'MFA code required' },
      },
    })
    loginMock.mockRejectedValueOnce(axiosError)

    const user = userEvent.setup()
    render(<LoginForm />)
    await fillAndSubmit(user)

    // MFA field should appear
    const mfaField = await screen.findByLabelText(/código de autenticación/i)
    expect(mfaField).toBeInTheDocument()
    expect(mfaField).toHaveAttribute('inputMode', 'numeric')
  })

  // ----------------------------------------------------------------
  // Error: network / unknown
  // ----------------------------------------------------------------
  it('error de red muestra toast de error genérico', async () => {
    const { toast } = await import('sonner')
    loginMock.mockRejectedValueOnce(new Error('Network Error'))

    const user = userEvent.setup()
    render(<LoginForm />)
    await fillAndSubmit(user)

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        'Error inesperado. Intentá nuevamente.'
      )
    })
  })

  // ----------------------------------------------------------------
  // Loading state
  // ----------------------------------------------------------------
  it('el botón muestra "Ingresando..." y está deshabilitado mientras se envía', async () => {
    // Login never resolves so we can inspect the in-flight state
    loginMock.mockImplementationOnce(
      () => new Promise<never>(() => undefined)
    )

    const user = userEvent.setup()
    render(<LoginForm />)
    await fillAndSubmit(user)

    const btn = await screen.findByRole('button', { name: /ingresando/i })
    expect(btn).toBeDisabled()
  })

  // ----------------------------------------------------------------
  // Link to register
  // ----------------------------------------------------------------
  it('el enlace "Registrarse" apunta a /register', () => {
    render(<LoginForm />)
    const link = screen.getByRole('link', { name: /registrarse/i })
    expect(link).toHaveAttribute('href', '/register')
  })
})
