'use client'

import { useState } from 'react'
import { FileText, FileSpreadsheet, Loader2, X } from 'lucide-react'
import { toast } from 'sonner'
import { isAxiosError } from 'axios'

import { reportsApi } from '@/lib/api/reports'
import type { ReportFilters, ReportFormat } from '@/types/report'
import { Button } from '@/components/ui/button'
import ReportPreview from './ReportPreview'
import VoiceReportControl from './VoiceReportControl'

const STATUS_OPTIONS = [
  { value: '', label: 'Todos los estados' },
  { value: 'registered', label: 'Registrado' },
  { value: 'in_review', label: 'En revisión' },
  { value: 'observed', label: 'Observado' },
  { value: 'docs_pending', label: 'Docs. pendientes' },
  { value: 'in_evaluation', label: 'En evaluación' },
  { value: 'approved', label: 'Aprobado' },
  { value: 'rejected', label: 'Rechazado' },
  { value: 'closed', label: 'Cerrado' },
]

// Etiqueta legible de un filtro resuelto por voz (analista, supervisor, asegurado).
interface ResolvedRef {
  id: string
  label: string
}

export default function ReportForm() {
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')
  const [status, setStatus] = useState('')
  const [q, setQ] = useState('')
  const [analyst, setAnalyst] = useState<ResolvedRef | null>(null)
  const [supervisor, setSupervisor] = useState<ResolvedRef | null>(null)
  const [policyholder, setPolicyholder] = useState<ResolvedRef | null>(null)
  const [downloading, setDownloading] = useState<ReportFormat | null>(null)

  const filters: ReportFilters = {
    format: 'pdf',
    from: from || undefined,
    to: to || undefined,
    status: status || undefined,
    q: q || undefined,
    analyst: analyst?.id,
    supervisor: supervisor?.id,
    policyholder: policyholder?.id,
  }

  const handleDownload = async (format: ReportFormat) => {
    setDownloading(format)
    try {
      await reportsApi.downloadClaimsReport({ ...filters, format })
      toast.success(`Reporte ${format.toUpperCase()} generado`)
    } catch (err) {
      if (isAxiosError(err) && err.response?.status === 403) {
        toast.error('No tenés permisos para generar reportes')
      } else {
        toast.error('Error al generar el reporte')
      }
    } finally {
      setDownloading(null)
    }
  }

  // Aplica los filtros que vinieron del pedido por voz (paso de confirmación).
  const applyVoiceFilters = (
    f: ReportFilters,
    interpretation: { resolved: { analyst_label?: string | null; supervisor_label?: string | null; policyholder_label?: string | null } }
  ) => {
    setFrom(f.from ?? '')
    setTo(f.to ?? '')
    setStatus(f.status ?? '')
    setQ(f.q ?? '')
    setAnalyst(f.analyst ? { id: f.analyst, label: interpretation.resolved.analyst_label ?? f.analyst } : null)
    setSupervisor(
      f.supervisor ? { id: f.supervisor, label: interpretation.resolved.supervisor_label ?? f.supervisor } : null
    )
    setPolicyholder(
      f.policyholder ? { id: f.policyholder, label: interpretation.resolved.policyholder_label ?? f.policyholder } : null
    )
  }

  const inputCls =
    'mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900'

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <div className="space-y-4 lg:col-span-2">
        <VoiceReportControl onApply={applyVoiceFilters} />

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-slate-700">Filtros del reporte</h2>
          <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
            <label className="block text-xs font-medium text-slate-500">
              Desde
              <input type="date" value={from} onChange={(e) => setFrom(e.target.value)} className={inputCls} />
            </label>
            <label className="block text-xs font-medium text-slate-500">
              Hasta
              <input type="date" value={to} onChange={(e) => setTo(e.target.value)} className={inputCls} />
            </label>
            <label className="block text-xs font-medium text-slate-500">
              Estado
              <select value={status} onChange={(e) => setStatus(e.target.value)} className={inputCls}>
                {STATUS_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="mt-4">
            <label className="block text-xs font-medium text-slate-500">
              Búsqueda libre (placa, expediente, lugar)
              <input
                type="text"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Ej.: ABC-123, EXP-2026-000004, Av. Busch"
                className={inputCls}
              />
            </label>
          </div>

          {(analyst || supervisor || policyholder) && (
            <div className="mt-4 flex flex-wrap gap-2">
              {analyst && (
                <FilterChip label={`Analista: ${analyst.label}`} onClear={() => setAnalyst(null)} />
              )}
              {supervisor && (
                <FilterChip label={`Supervisor: ${supervisor.label}`} onClear={() => setSupervisor(null)} />
              )}
              {policyholder && (
                <FilterChip
                  label={`Asegurado: ${policyholder.label}`}
                  onClear={() => setPolicyholder(null)}
                />
              )}
            </div>
          )}

          <div className="mt-5 flex flex-wrap gap-3">
            <Button onClick={() => handleDownload('pdf')} disabled={downloading !== null}>
              {downloading === 'pdf' ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <FileText className="mr-2 h-4 w-4" />
              )}
              Generar PDF
            </Button>
            <Button
              variant="outline"
              onClick={() => handleDownload('xlsx')}
              disabled={downloading !== null}
            >
              {downloading === 'xlsx' ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <FileSpreadsheet className="mr-2 h-4 w-4" />
              )}
              Generar Excel
            </Button>
          </div>
        </div>
      </div>

      <ReportPreview filters={filters} />
    </div>
  )
}

function FilterChip({ label, onClear }: { label: string; onClear: () => void }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-indigo-100 px-3 py-1 text-xs font-medium text-indigo-700">
      {label}
      <button type="button" onClick={onClear} className="rounded-full hover:bg-indigo-200">
        <X className="h-3 w-3" />
      </button>
    </span>
  )
}
