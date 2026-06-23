import type { ReportFilters } from '@/types/report'

const STATUS_LABELS: Record<string, string> = {
  registered: 'Registrado',
  in_review: 'En revisión',
  observed: 'Observado',
  docs_pending: 'Docs. pendientes',
  in_evaluation: 'En evaluación',
  approved: 'Aprobado',
  rejected: 'Rechazado',
  closed: 'Cerrado',
}

export default function ReportPreview({ filters }: { filters: ReportFilters }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm">
      <h3 className="mb-2 font-semibold text-slate-700">Resumen del reporte</h3>
      <ul className="space-y-1 text-slate-600">
        <li>
          <span className="font-medium">Formato:</span>{' '}
          {filters.format === 'pdf' ? 'PDF' : 'Excel (.xlsx)'}
        </li>
        <li>
          <span className="font-medium">Rango:</span>{' '}
          {filters.from || filters.to
            ? `${filters.from || '…'} → ${filters.to || '…'}`
            : 'Todo el histórico'}
        </li>
        <li>
          <span className="font-medium">Estado:</span>{' '}
          {filters.status ? STATUS_LABELS[filters.status] ?? filters.status : 'Todos'}
        </li>
        {filters.q && (
          <li>
            <span className="font-medium">Búsqueda:</span> {filters.q}
          </li>
        )}
      </ul>
    </div>
  )
}
