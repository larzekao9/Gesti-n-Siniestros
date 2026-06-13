'use client'

import { TrendingDown, TrendingUp } from 'lucide-react'
import type { AIAnalysis, FraudFactor } from '@/types/ai-analysis'

// Medidor + lista de factores heurísticos (ADR-010) — reemplaza el panel SHAP.
export default function FraudScoreCard({ analysis }: { analysis: AIAnalysis }) {
  const score = typeof analysis.score === 'number' ? analysis.score : Number(analysis.score ?? 0)
  const factors = ((analysis.payload?.factors as FraudFactor[] | undefined) ?? [])

  const color =
    score > 0.85 ? { bar: 'bg-red-500', text: 'text-red-700', label: 'Riesgo alto' }
    : score > 0.5 ? { bar: 'bg-yellow-500', text: 'text-yellow-700', label: 'Riesgo medio' }
    : { bar: 'bg-green-500', text: 'text-green-700', label: 'Riesgo bajo' }

  return (
    <div className="space-y-4">
      <div>
        <div className="flex items-baseline justify-between mb-1">
          <span className={`text-2xl font-bold ${color.text}`}>{(score * 100).toFixed(0)}%</span>
          <span className={`text-sm font-medium ${color.text}`}>{color.label}</span>
        </div>
        <div className="h-3 w-full rounded-full bg-slate-100 overflow-hidden">
          <div className={`h-full rounded-full transition-all ${color.bar}`} style={{ width: `${Math.min(100, score * 100)}%` }} />
        </div>
      </div>

      {factors.length > 0 && (
        <ul className="space-y-1.5">
          {factors.map((f, i) => (
            <li key={i} className="flex items-center justify-between gap-2 text-sm">
              <span className="flex items-center gap-2 text-slate-700 min-w-0">
                {f.direction === 'up'
                  ? <TrendingUp className="h-3.5 w-3.5 text-red-500 shrink-0" />
                  : <TrendingDown className="h-3.5 w-3.5 text-green-600 shrink-0" />}
                <span className="truncate">{f.name}</span>
              </span>
              <span className={`font-mono text-xs ${f.direction === 'up' ? 'text-red-600' : 'text-green-600'}`}>
                {f.contribution > 0 ? '+' : ''}{f.contribution.toFixed(2)}
              </span>
            </li>
          ))}
        </ul>
      )}

      {analysis.explanation && (
        <p className="text-xs text-slate-500 border-t border-slate-100 pt-2">{analysis.explanation}</p>
      )}
    </div>
  )
}
