import apiClient from './client'
import type { ReportFilters, VoiceReportInterpretation } from '@/types/report'

function filenameFromDisposition(header: string | undefined, fallback: string): string {
  if (!header) return fallback
  const match = /filename="?([^"]+)"?/.exec(header)
  return match ? match[1] : fallback
}

export const reportsApi = {
  /** Descarga el reporte de siniestros como archivo (PDF o Excel). */
  downloadClaimsReport: async (filters: ReportFilters): Promise<void> => {
    const { format, from, to, status, analyst, supervisor, policyholder, q } = filters
    const response = await apiClient.get('/reports/claims', {
      params: {
        format,
        ...(from ? { from } : {}),
        ...(to ? { to } : {}),
        ...(status ? { status } : {}),
        ...(analyst ? { analyst } : {}),
        ...(supervisor ? { supervisor } : {}),
        ...(policyholder ? { policyholder } : {}),
        ...(q ? { q } : {}),
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

  /**
   * CU-37 — Envía el audio grabado al backend (Whisper) y devuelve la
   * transcripción + los filtros interpretados para confirmar antes de generar.
   */
  interpretVoice: async (audio: Blob): Promise<VoiceReportInterpretation> => {
    const form = new FormData()
    const ext = audio.type.includes('ogg') ? 'ogg' : 'webm'
    form.append('audio', audio, `pedido.${ext}`)
    // Sobrescribimos el Content-Type por defecto (application/json) del cliente:
    // con ese header axios serializaría el FormData a JSON y perdería el audio.
    // Pasándolo como multipart, el navegador agrega el boundary correcto.
    const response = await apiClient.post('/reports/voice', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data as VoiceReportInterpretation
  },
}
