import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

const downloadMock = vi.fn().mockResolvedValue(undefined)
vi.mock('@/lib/api/reports', () => ({
  reportsApi: { downloadClaimsReport: (...args: unknown[]) => downloadMock(...args) },
}))

import ReportForm from '@/components/reports/ReportForm'

describe('ReportForm', () => {
  beforeEach(() => downloadMock.mockClear())

  it('downloads a PDF report with the selected format', async () => {
    const user = userEvent.setup()
    render(<ReportForm />)
    await user.click(screen.getByRole('button', { name: /Generar PDF/i }))
    await waitFor(() => expect(downloadMock).toHaveBeenCalledTimes(1))
    expect(downloadMock.mock.calls[0][0]).toMatchObject({ format: 'pdf' })
  })

  it('downloads an Excel report when clicking Generar Excel', async () => {
    const user = userEvent.setup()
    render(<ReportForm />)
    await user.click(screen.getByRole('button', { name: /Generar Excel/i }))
    await waitFor(() => expect(downloadMock).toHaveBeenCalledTimes(1))
    expect(downloadMock.mock.calls[0][0]).toMatchObject({ format: 'xlsx' })
  })
})
