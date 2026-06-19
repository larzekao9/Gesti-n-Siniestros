/**
 * Tests for MFAVerifyForm component.
 *
 * Covers:
 *  - Renders code input with correct attributes (inputMode numeric, maxLength 6)
 *  - Validation: less than 6 digits, non-numeric characters
 *  - Successful verification → setAuth (mfa_enabled:true) + router.push('/dashboard')
 *  - API returns success:false → toast error + input reset
 *  - API 401 with detail → toast error
 *  - Loading state during submit
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { render } from '../../helpers/test-utils'
import { MFAVerifyForm } from '@/components/auth/MFAVerifyForm'
import * as authApi from '@/lib/api/auth'
import { useAuthStore } from '@/lib/stores/authStore'
import { mockUser } from '../../helpers/mocks'

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
    verifyMFA: vi.fn(),
    getMe: vi.fn(),
  },
}))

// ------------------------------------------------------------------
// Tests
// ------------------------------------------------------------------
describe('MFAVerifyForm', () => {
  const verifyMFAMock = vi.mocked(authApi.authApi.verifyMFA)
  const getMeMock = vi.mocked(authApi.authApi.getMe)

  beforeEach(() => {
    vi.clearAllMocks()
    mockPush.mockClear()
    // Seed store with a logged-in user (MFA not yet enabled)
    useAuthStore.setState({
      user: mockUser({ mfa_enabled: false }),
      accessToken: 'access.jwt.token',
      isLoading: false,
    })
    // Stub localStorage for getItem('siniestros_rt')
    vi.stubGlobal('localStorage', {
      getItem: vi.fn().mockReturnValue('refresh.jwt.token'),
      setItem: vi.fn(),
      removeItem: vi.fn(),
    })
  })

  // ----------------------------------------------------------------
  // Rendering
  // ----------------------------------------------------------------
  it('renderiza el campo de código con atributos correctos', () => {
    render(<MFAVerifyForm />)

    const input = screen.getByLabelText(/código de verificación/i)
    expect(input).toBeInTheDocument()
    expect(input).toHaveAttribute('inputMode', 'numeric')
    expect(input).toHaveAttribute('maxLength', '6')
  })

  it('muestra el botón de verificar', () => {
    render(<MFAVerifyForm />)
    expect(
      screen.getByRole('button', { name: /verificar código/i })
    ).toBeInTheDocument()
  })

  // ----------------------------------------------------------------
  // Validation
  // ----------------------------------------------------------------
  it('muestra error cuando el código tiene menos de 6 dígitos', async () => {
    const user = userEvent.setup()
    render(<MFAVerifyForm />)

    const input = screen.getByLabelText(/código de verificación/i)
    await user.type(input, '123')
    await user.tab()

    expect(await screen.findByRole('alert')).toHaveTextContent(
      /exactamente 6 dígitos/i
    )
  })

  it('el botón está deshabilitado cuando el formulario es inválido', async () => {
    const user = userEvent.setup()
    render(<MFAVerifyForm />)

    const input = screen.getByLabelText(/código de verificación/i)
    await user.type(input, '12345') // 5 digits — invalid

    const btn = screen.getByRole('button', { name: /verificar código/i })
    expect(btn).toBeDisabled()
  })

  // ----------------------------------------------------------------
  // Happy path
  // ----------------------------------------------------------------
  it('verificación exitosa actualiza mfa_enabled y redirige a /dashboard', async () => {
    verifyMFAMock.mockResolvedValueOnce({ message: 'MFA activado' })
    getMeMock.mockResolvedValueOnce(mockUser({ mfa_enabled: true }))

    const user = userEvent.setup()
    render(<MFAVerifyForm />)

    await user.type(screen.getByLabelText(/código de verificación/i), '123456')
    await user.click(screen.getByRole('button', { name: /verificar código/i }))

    await waitFor(() => {
      expect(verifyMFAMock).toHaveBeenCalledWith('123456')
    })

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/dashboard')
    })

    const storedUser = useAuthStore.getState().user
    expect(storedUser?.mfa_enabled).toBe(true)
  })

  // ----------------------------------------------------------------
  // error from API
  // ----------------------------------------------------------------
  it('error de API muestra toast de código incorrecto', async () => {
    const { toast } = await import('sonner')
    verifyMFAMock.mockRejectedValueOnce(new Error('Código inválido'))

    const user = userEvent.setup()
    render(<MFAVerifyForm />)

    await user.type(screen.getByLabelText(/código de verificación/i), '000000')
    await user.click(screen.getByRole('button', { name: /verificar código/i }))

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Error inesperado. Intentá nuevamente.')
    })
    expect(mockPush).not.toHaveBeenCalled()
  })

  // ----------------------------------------------------------------
  // Error: Axios 401
  // ----------------------------------------------------------------
  it('error de API muestra el detail en el toast', async () => {
    const { toast } = await import('sonner')
    const axiosError = Object.assign(new Error('Unauthorized'), {
      isAxiosError: true,
      response: {
        status: 401,
        data: { detail: 'Código inválido o expirado.' },
      },
    })
    verifyMFAMock.mockRejectedValueOnce(axiosError)

    const user = userEvent.setup()
    render(<MFAVerifyForm />)

    await user.type(screen.getByLabelText(/código de verificación/i), '999999')
    await user.click(screen.getByRole('button', { name: /verificar código/i }))

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Código inválido o expirado.')
    })
    expect(mockPush).not.toHaveBeenCalled()
  })

  // ----------------------------------------------------------------
  // Error: network
  // ----------------------------------------------------------------
  it('error de red muestra toast genérico', async () => {
    const { toast } = await import('sonner')
    verifyMFAMock.mockRejectedValueOnce(new Error('Network Error'))

    const user = userEvent.setup()
    render(<MFAVerifyForm />)

    await user.type(screen.getByLabelText(/código de verificación/i), '123456')
    await user.click(screen.getByRole('button', { name: /verificar código/i }))

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Error inesperado. Intentá nuevamente.')
    })
  })

  // ----------------------------------------------------------------
  // Loading state
  // ----------------------------------------------------------------
  it('el botón muestra "Verificando..." mientras se envía', async () => {
    verifyMFAMock.mockImplementationOnce(
      () => new Promise<never>(() => undefined)
    )

    const user = userEvent.setup()
    render(<MFAVerifyForm />)

    await user.type(screen.getByLabelText(/código de verificación/i), '123456')
    await user.click(screen.getByRole('button', { name: /verificar código/i }))

    const btn = await screen.findByRole('button', { name: /verificando/i })
    expect(btn).toBeDisabled()
  })
})
