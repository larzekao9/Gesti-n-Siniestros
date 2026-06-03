'use client'

import type { AuditFilters as Filters } from '@/types/audit'
import { ACTION_LABELS } from '@/lib/api/audit'
import { Button } from '@/components/ui/button'

interface Props {
  filters: Filters
  onChange: (patch: Partial<Filters>) => void
  onClear: () => void
}

const ENTITY_OPTIONS = [
  { value: '', label: 'Todas las entidades' },
  { value: 'claim', label: 'Expediente' },
  { value: 'claim_request', label: 'Solicitud' },
  { value: 'document_request', label: 'Documentación' },
  { value: 'evidence', label: 'Evidencia' },
  { value: 'report', label: 'Reporte' },
]

export default function AuditFilters({ filters, onChange, onClear }: Props) {
  const inputCls =
    'mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900'

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <label className="block text-xs font-medium text-slate-500">
          Acción
          <select
            value={filters.action ?? ''}
            onChange={(e) => onChange({ action: e.target.value || undefined })}
            className={inputCls}
          >
            <option value="">Todas las acciones</option>
            {Object.entries(ACTION_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label className="block text-xs font-medium text-slate-500">
          Entidad
          <select
            value={filters.entity_type ?? ''}
            onChange={(e) => onChange({ entity_type: e.target.value || undefined })}
            className={inputCls}
          >
            {ENTITY_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>
        <label className="block text-xs font-medium text-slate-500">
          Desde
          <input
            type="date"
            value={filters.from ?? ''}
            onChange={(e) => onChange({ from: e.target.value || undefined })}
            className={inputCls}
          />
        </label>
        <label className="block text-xs font-medium text-slate-500">
          Hasta
          <input
            type="date"
            value={filters.to ?? ''}
            onChange={(e) => onChange({ to: e.target.value || undefined })}
            className={inputCls}
          />
        </label>
      </div>
      <div className="mt-3 flex justify-end">
        <Button variant="ghost" size="sm" onClick={onClear}>
          Limpiar filtros
        </Button>
      </div>
    </div>
  )
}
