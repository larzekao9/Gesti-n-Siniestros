'use client'

import { useCallback, useEffect, useState } from 'react'
import { FileText, FolderOpen, CheckCircle2, XCircle, Clock, ShieldAlert } from 'lucide-react'
import { toast } from 'sonner'
import { isAxiosError } from 'axios'

import { analyticsApi } from '@/lib/api/analytics'
import type {
  AIKPIs,
  AnalystProductivityItem,
  CoverageDistributionItem,
  KPIs,
  StatusDistributionItem,
  TimelinePoint,
} from '@/types/analytics'
import KPICard from '@/components/dashboard/KPICard'
import ClaimsByStatusChart from '@/components/dashboard/ClaimsByStatusChart'
import ClaimsTimelineChart from '@/components/dashboard/ClaimsTimelineChart'
import CoveragePieChart from '@/components/dashboard/CoveragePieChart'
import { Button } from '@/components/ui/button'

export default function DashboardPage() {
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')
  const [kpis, setKpis] = useState<KPIs | null>(null)
  const [statusDist, setStatusDist] = useState<StatusDistributionItem[]>([])
  const [timeline, setTimeline] = useState<TimelinePoint[]>([])
  const [coverage, setCoverage] = useState<CoverageDistributionItem[]>([])
  const [productivity, setProductivity] = useState<AnalystProductivityItem[]>([])
  const [aiKpis, setAiKpis] = useState<AIKPIs | null>(null)
  const [loading, setLoading] = useState(true)
  const [forbidden, setForbidden] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    const params = {
      ...(from ? { from } : {}),
      ...(to ? { to } : {}),
    }
    try {
      const [k, sd, tl, cov, prod, ai] = await Promise.all([
        analyticsApi.kpis(params),
        analyticsApi.statusDistribution(params),
        analyticsApi.timeline(params),
        analyticsApi.coverageDistribution(),
        analyticsApi.analystProductivity(params),
        analyticsApi.aiKpis(),
      ])
      setKpis(k)
      setStatusDist(sd.items)
      setTimeline(tl.items)
      setCoverage(cov.items)
      setProductivity(prod.items)
      setAiKpis(ai)
      setForbidden(false)
    } catch (err) {
      if (isAxiosError(err) && err.response?.status === 403) {
        setForbidden(true)
      } else {
        toast.error('Error al cargar los indicadores')
      }
    } finally {
      setLoading(false)
    }
  }, [from, to])

  useEffect(() => {
    load()
  }, [load])

  if (forbidden) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-6 text-amber-800">
          El dashboard de indicadores está disponible solo para supervisores y administradores.
        </div>
      </div>
    )
  }

  const pct = (v: number | undefined) =>
    v === undefined ? '—' : `${(v * 100).toFixed(1)}%`

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
          <p className="mt-1 text-slate-500">Indicadores operativos del tenant</p>
        </div>
        <div className="flex items-end gap-2">
          <label className="flex flex-col text-xs font-medium text-slate-500">
            Desde
            <input
              type="date"
              value={from}
              onChange={(e) => setFrom(e.target.value)}
              className="mt-1 rounded-md border border-slate-300 px-2 py-1.5 text-sm text-slate-900"
            />
          </label>
          <label className="flex flex-col text-xs font-medium text-slate-500">
            Hasta
            <input
              type="date"
              value={to}
              onChange={(e) => setTo(e.target.value)}
              className="mt-1 rounded-md border border-slate-300 px-2 py-1.5 text-sm text-slate-900"
            />
          </label>
          {(from || to) && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setFrom('')
                setTo('')
              }}
            >
              Limpiar
            </Button>
          )}
        </div>
      </div>

      {loading && !kpis ? (
        <div className="py-20 text-center text-slate-400">Cargando indicadores…</div>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
            <KPICard label="Expedientes" value={kpis?.total_claims ?? 0} icon={FileText} accent="blue" />
            <KPICard label="Abiertos" value={kpis?.open_claims ?? 0} icon={FolderOpen} accent="amber" />
            <KPICard label="Tasa de aprobación" value={pct(kpis?.approval_rate)} icon={CheckCircle2} accent="green" />
            <KPICard label="Rechazo en intake" value={pct(kpis?.intake_rejection_rate)} icon={XCircle} accent="red" />
            <KPICard
              label="Días prom. a decisión"
              value={kpis?.avg_days_to_decision ?? '—'}
              icon={Clock}
              accent="slate"
            />
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <ClaimsTimelineChart data={timeline} />
            <ClaimsByStatusChart data={statusDist} />
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <CoveragePieChart data={coverage} />
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h3 className="text-sm font-semibold text-slate-700">Productividad por analista</h3>
              {productivity.length === 0 ? (
                <p className="py-16 text-center text-sm text-slate-400">Sin datos</p>
              ) : (
                <table className="mt-3 w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-200 text-left text-xs text-slate-500">
                      <th className="pb-2">Analista</th>
                      <th className="pb-2 text-right">Asignados</th>
                      <th className="pb-2 text-right">Decididos</th>
                    </tr>
                  </thead>
                  <tbody>
                    {productivity.map((p) => (
                      <tr key={p.analyst_id} className="border-b border-slate-100 last:border-0">
                        <td className="py-2 text-slate-700">{p.analyst_name}</td>
                        <td className="py-2 text-right font-medium text-slate-900">{p.assigned}</td>
                        <td className="py-2 text-right font-medium text-slate-900">{p.decided}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>

          {/* Fase 2 de CU-21 (Ciclo 8): KPIs de IA */}
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center gap-2">
              <ShieldAlert className="h-4 w-4 text-purple-600" />
              <h3 className="text-sm font-semibold text-slate-700">Análisis inteligente (IA)</h3>
            </div>
            <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div>
                <p className="text-2xl font-bold text-red-600">{aiKpis?.suspicious_claims ?? 0}</p>
                <p className="text-xs text-slate-500">
                  Casos sospechosos (score &gt; {((aiKpis?.fraud_alert_threshold ?? 0.85) * 100).toFixed(0)}%)
                </p>
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-900">{pct(aiKpis?.high_fraud_rate)}</p>
                <p className="text-xs text-slate-500">
                  % con fraud score alto ({aiKpis?.scored_claims ?? 0} analizados)
                </p>
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-900">{aiKpis?.total_inconsistency_findings ?? 0}</p>
                <p className="text-xs text-slate-500">Inconsistencias detectadas (total)</p>
              </div>
            </div>
            {aiKpis && aiKpis.top_inconsistencies.length > 0 && (
              <div className="mt-4 border-t border-slate-100 pt-3">
                <p className="text-xs font-medium text-slate-500">Campos más inconsistentes</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {aiKpis.top_inconsistencies.map((t) => (
                    <span
                      key={t.field}
                      className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-1 text-xs text-amber-800"
                    >
                      <span className="font-mono">{t.field}</span>
                      <span className="font-semibold">{t.count}</span>
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
