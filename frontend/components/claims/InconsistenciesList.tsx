'use client'

import { AlertTriangle, Info, OctagonAlert } from 'lucide-react'
import type { AIAnalysis, InconsistencyFinding } from '@/types/ai-analysis'

const SEVERITY_STYLE: Record<string, { icon: typeof Info; chip: string; label: string }> = {
  info: { icon: Info, chip: 'bg-blue-100 text-blue-700', label: 'Info' },
  warning: { icon: AlertTriangle, chip: 'bg-yellow-100 text-yellow-700', label: 'Advertencia' },
  critical: { icon: OctagonAlert, chip: 'bg-red-100 text-red-700', label: 'Crítica' },
}

export default function InconsistenciesList({ analysis }: { analysis: AIAnalysis }) {
  const findings = ((analysis.payload?.findings as InconsistencyFinding[] | undefined) ?? [])

  if (findings.length === 0) {
    return (
      <p className="text-sm text-green-700 bg-green-50 rounded-md px-3 py-2">
        ✓ Sin inconsistencias detectadas entre la declaración, la póliza y los documentos.
      </p>
    )
  }

  return (
    <ul className="space-y-2">
      {findings.map((f, i) => {
        const style = SEVERITY_STYLE[f.severity] ?? SEVERITY_STYLE.info
        const Icon = style.icon
        return (
          <li key={i} className="flex items-start gap-3 rounded-md border border-slate-200 p-3">
            <Icon className="h-4 w-4 mt-0.5 shrink-0 text-slate-500" />
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${style.chip}`}>{style.label}</span>
                {f.field && <span className="text-xs text-slate-400 font-mono truncate">{f.field}</span>}
              </div>
              <p className="text-sm text-slate-700 mt-1">{f.message}</p>
            </div>
          </li>
        )
      })}
    </ul>
  )
}
