'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowUpRight, FileText } from 'lucide-react'
import { claimsApi } from '@/lib/api/claims'
import { useAuthStore } from '@/lib/stores/authStore'
import { Button } from '@/components/ui/button'
import type { Claim } from '@/types/claim'

const STATUS_MAP: Record<string, { label: string; color: string }> = {
  registered: { label: 'Registrado', color: 'bg-gray-100 text-gray-700' },
  in_review: { label: 'En revisión', color: 'bg-blue-100 text-blue-700' },
  observed: { label: 'Observado', color: 'bg-yellow-100 text-yellow-700' },
  docs_pending: { label: 'Docs pendientes', color: 'bg-orange-100 text-orange-700' },
  in_evaluation: { label: 'En evaluación', color: 'bg-purple-100 text-purple-700' },
  approved: { label: 'Aprobado', color: 'bg-green-100 text-green-700' },
  rejected: { label: 'Rechazado', color: 'bg-red-100 text-red-700' },
  closed: { label: 'Cerrado', color: 'bg-gray-200 text-gray-500' },
}

export default function CasosEscaladosPage() {
  const router = useRouter()
  const user = useAuthStore((s) => s.user)
  const [claims, setClaims] = useState<Claim[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user?.id) return
    const load = async () => {
      try {
        // Server-side filter: solo los expedientes escalados a ESTE supervisor
        const res = await claimsApi.list({ page: 1, limit: 100, supervisor: user.id })
        setClaims(res.items.filter((c) => c.status !== 'closed'))
      } catch {
        // silently fail — list will be empty
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [user?.id])

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">Casos escalados</h1>
        <p className="text-sm text-slate-500 mt-1">
          Expedientes que requieren tu revisión como supervisor
        </p>
      </div>

      {loading ? (
        <div className="text-center py-12 text-slate-500">Cargando...</div>
      ) : claims.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg border border-slate-200">
          <FileText className="h-10 w-10 mx-auto mb-3 text-slate-300" />
          <p className="text-slate-500 font-medium">Sin casos escalados</p>
          <p className="text-sm text-slate-400 mt-1">No hay expedientes pendientes de revisión</p>
        </div>
      ) : (
        <div className="space-y-3">
          {claims.map((c) => (
            <div
              key={c.id}
              className="p-4 bg-white rounded-lg border border-slate-200 hover:border-blue-300 transition-colors cursor-pointer"
              onClick={() => router.push(`/dashboard/expedientes/${c.id}`)}
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm font-medium text-slate-700">
                      {c.claim_number}
                    </span>
                    <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${STATUS_MAP[c.status]?.color || 'bg-gray-100 text-gray-700'}`}>
                      {STATUS_MAP[c.status]?.label || c.status}
                    </span>
                  </div>
                  <p className="text-sm text-slate-500 mt-1">
                    {c.policyholder?.full_name || 'Sin asegurado'} — {c.accident_location}
                  </p>
                </div>
                <ArrowUpRight className="h-4 w-4 text-slate-400" />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
