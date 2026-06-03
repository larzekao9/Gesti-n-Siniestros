'use client'

import ReportForm from '@/components/reports/ReportForm'

export default function ReportesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Reportes operativos</h1>
        <p className="mt-1 text-slate-500">
          Generá reportes de siniestros en PDF o Excel con los filtros que necesites.
        </p>
      </div>
      <ReportForm />
    </div>
  )
}
