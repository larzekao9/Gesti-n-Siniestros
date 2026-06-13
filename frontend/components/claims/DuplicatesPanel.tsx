'use client'

import Link from 'next/link'
import { Copy, ExternalLink } from 'lucide-react'
import type { AIAnalysis, DuplicateMatch } from '@/types/ai-analysis'

export default function DuplicatesPanel({ analysis }: { analysis: AIAnalysis }) {
  const matches = ((analysis.payload?.matches as DuplicateMatch[] | undefined) ?? [])

  if (matches.length === 0) {
    return (
      <p className="text-sm text-green-700 bg-green-50 rounded-md px-3 py-2">
        ✓ No se encontraron expedientes similares por encima del umbral.
      </p>
    )
  }

  return (
    <div className="space-y-2">
      {matches.map((m) => (
        <div key={m.claim_id} className="flex items-center justify-between rounded-md border border-amber-200 bg-amber-50 p-3">
          <div className="flex items-center gap-3">
            <Copy className="h-4 w-4 text-amber-600" />
            <div>
              <p className="text-sm font-medium text-slate-800">{m.claim_number}</p>
              <p className="text-xs text-slate-500">Similitud: {(m.similarity * 100).toFixed(1)}%</p>
            </div>
          </div>
          {/* CTA "Ver expediente comparado" (CU-32 flujo 3) */}
          <Link
            href={`/dashboard/expedientes/${m.claim_id}`}
            className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800"
          >
            Ver expediente <ExternalLink className="h-3.5 w-3.5" />
          </Link>
        </div>
      ))}
    </div>
  )
}
