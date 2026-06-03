// Tipos para reportes operativos (CU-22).

export type ReportFormat = 'pdf' | 'xlsx'

export interface ReportFilters {
  format: ReportFormat
  from?: string
  to?: string
  status?: string
  analyst?: string
}
