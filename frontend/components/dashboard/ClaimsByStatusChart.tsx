'use client'

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { StatusDistributionItem } from '@/types/analytics'

const STATUS_LABELS: Record<string, string> = {
  registered: 'Registrado',
  in_review: 'En revisión',
  observed: 'Observado',
  docs_pending: 'Docs. pend.',
  in_evaluation: 'En evaluación',
  approved: 'Aprobado',
  rejected: 'Rechazado',
  closed: 'Cerrado',
}

const STATUS_COLORS: Record<string, string> = {
  registered: '#64748b',
  in_review: '#3b82f6',
  observed: '#f59e0b',
  docs_pending: '#eab308',
  in_evaluation: '#8b5cf6',
  approved: '#10b981',
  rejected: '#ef4444',
  closed: '#0f172a',
}

export default function ClaimsByStatusChart({
  data,
}: {
  data: StatusDistributionItem[]
}) {
  const chartData = data.map((d) => ({
    name: STATUS_LABELS[d.status] ?? d.status,
    status: d.status,
    count: d.count,
  }))

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-700">Expedientes por estado</h3>
      {chartData.length === 0 ? (
        <p className="py-16 text-center text-sm text-slate-400">Sin datos</p>
      ) : (
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={chartData} margin={{ top: 16, right: 8, bottom: 8, left: -16 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
            <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} angle={-20} textAnchor="end" height={50} />
            <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
            <Tooltip />
            <Bar dataKey="count" name="Expedientes" radius={[4, 4, 0, 0]}>
              {chartData.map((entry) => (
                <Cell key={entry.status} fill={STATUS_COLORS[entry.status] ?? '#3b82f6'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
