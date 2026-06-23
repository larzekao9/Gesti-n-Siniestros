// Tipos para reportes operativos (CU-22) y reportes por voz (CU-37).

export type ReportFormat = 'pdf' | 'xlsx'

export interface ReportFilters {
  format: ReportFormat
  from?: string
  to?: string
  status?: string
  analyst?: string
  supervisor?: string
  policyholder?: string
  q?: string
}

// ── CU-37: interpretación de un pedido de reporte por voz ──────────────

export interface VoiceReportResolved {
  format: string
  status_label?: string | null
  analyst_label?: string | null
  supervisor_label?: string | null
  policyholder_label?: string | null
}

export interface VoiceReportInterpretation {
  transcript: string
  supported: boolean
  note: string
  filters: {
    format: ReportFormat
    status?: string | null
    from?: string | null
    to?: string | null
    analyst?: string | null
    supervisor?: string | null
    policyholder?: string | null
    q?: string | null
  }
  resolved: VoiceReportResolved
  warnings: string[]
}
