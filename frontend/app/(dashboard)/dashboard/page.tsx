import type { Metadata } from 'next'
import { LayoutDashboard } from 'lucide-react'

export const metadata: Metadata = {
  title: 'Dashboard | Gestión Siniestros',
}

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
        <p className="text-slate-500 mt-1">Resumen general de la plataforma</p>
      </div>

      {/* Sprint 5 placeholder */}
      <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-200 bg-white py-20 gap-4">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-blue-50">
          <LayoutDashboard className="h-8 w-8 text-blue-400" aria-hidden="true" />
        </div>
        <div className="text-center space-y-1">
          <p className="text-lg font-semibold text-slate-700">Dashboard — Sprint 5</p>
          <p className="text-sm text-slate-400 max-w-xs">
            Los KPIs, gráficas y métricas en tiempo real se implementarán en el Sprint 5.
          </p>
        </div>
        <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-700">
          Pendiente
        </span>
      </div>
    </div>
  )
}
