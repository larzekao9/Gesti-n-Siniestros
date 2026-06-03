'use client'

import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import type { CoverageDistributionItem } from '@/types/analytics'

const COLORS = ['#2563eb', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#06b6d4', '#64748b']

export default function CoveragePieChart({
  data,
}: {
  data: CoverageDistributionItem[]
}) {
  const chartData = data.map((d) => ({ name: d.coverage_type, value: d.count }))

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-700">Cobertura de pólizas</h3>
      {chartData.length === 0 ? (
        <p className="py-16 text-center text-sm text-slate-400">Sin datos</p>
      ) : (
        <ResponsiveContainer width="100%" height={260}>
          <PieChart>
            <Pie
              data={chartData}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              outerRadius={90}
              label={(entry) => `${entry.name}: ${entry.value}`}
              labelLine={false}
            >
              {chartData.map((entry, idx) => (
                <Cell key={entry.name} fill={COLORS[idx % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
