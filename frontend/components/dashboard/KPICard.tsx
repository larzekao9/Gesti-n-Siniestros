import type { ComponentType } from 'react'

interface KPICardProps {
  label: string
  value: string | number
  icon?: ComponentType<{ className?: string }>
  hint?: string
  accent?: 'blue' | 'green' | 'amber' | 'red' | 'slate'
}

const ACCENTS: Record<NonNullable<KPICardProps['accent']>, string> = {
  blue: 'bg-blue-50 text-blue-600',
  green: 'bg-emerald-50 text-emerald-600',
  amber: 'bg-amber-50 text-amber-600',
  red: 'bg-red-50 text-red-600',
  slate: 'bg-slate-100 text-slate-600',
}

export default function KPICard({
  label,
  value,
  icon: Icon,
  hint,
  accent = 'blue',
}: KPICardProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-slate-500">{label}</p>
          <p className="mt-2 text-3xl font-bold text-slate-900">{value}</p>
          {hint && <p className="mt-1 text-xs text-slate-400">{hint}</p>}
        </div>
        {Icon && (
          <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${ACCENTS[accent]}`}>
            <Icon className="h-5 w-5" />
          </div>
        )}
      </div>
    </div>
  )
}
