import apiClient from './client'
import type { ReportFilters } from '@/types/report'

function filenameFromDisposition(header: string | undefined, fallback: string): string {
  if (!header) return fallback
  const match = /filename="?([^"]+)"?/.exec(header)
  return match ? match[1] : fallback
}

export const reportsApi = {
  /** Descarga el reporte de siniestros como archivo (PDF o Excel). */
  downloadClaimsReport: async (filters: ReportFilters): Promise<void> => {
    const { format, from, to, status, analyst } = filters
    const response = await apiClient.get('/reports/claims', {
      params: {
        format,
        ...(from ? { from } : {}),
        ...(to ? { to } : {}),
        ...(status ? { status } : {}),
        ...(analyst ? { analyst } : {}),
      },
      responseType: 'blob',
    })

    const fallback = `reporte_siniestros.${format}`
    const filename = filenameFromDisposition(
      response.headers['content-disposition'],
      fallback
    )

    const blob = new Blob([response.data])
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  },
}
