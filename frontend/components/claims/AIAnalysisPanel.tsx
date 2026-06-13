'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { toast } from 'sonner'
import { Bot, Camera, Loader2, RefreshCw, ShieldAlert, Copy, SearchCheck } from 'lucide-react'
import { aiAnalysesApi } from '@/lib/api/ai-analyses'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import InconsistenciesList from './InconsistenciesList'
import DuplicatesPanel from './DuplicatesPanel'
import FraudScoreCard from './FraudScoreCard'
import type { AIAnalysis, AIAnalysisKind, DamageAssessment } from '@/types/ai-analysis'

const POLL_MS = 5000 // F-A1: polling mientras haya análisis en proceso

interface Props {
  claimId: string
  userRole?: string | null
}

export default function AIAnalysisPanel({ claimId, userRole }: Props) {
  const [items, setItems] = useState<AIAnalysis[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const load = useCallback(async () => {
    try {
      const r = await aiAnalysesApi.listForClaim(claimId)
      setItems(r.items)
      return r.items
    } catch {
      toast.error('Error al cargar análisis IA')
      return []
    } finally {
      setLoading(false)
    }
  }, [claimId])

  // Carga inicial + polling condicionado a "processing"
  useEffect(() => {
    load()
  }, [load])

  useEffect(() => {
    const anyProcessing = items.some((i) => i.status === 'processing')
    if (anyProcessing && !pollRef.current) {
      pollRef.current = setInterval(load, POLL_MS)
    }
    if (!anyProcessing && pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
    return () => {
      if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null }
    }
  }, [items, load])

  const canRefresh = userRole === 'supervisor' || userRole === 'admin'

  const handleRefresh = async () => {
    setRefreshing(true)
    try {
      await aiAnalysesApi.refresh(claimId)
      toast.success('Análisis encolado — los resultados aparecerán en unos segundos')
      setTimeout(load, 2500)
    } catch {
      toast.error('No se pudo re-ejecutar el análisis')
    } finally {
      setRefreshing(false)
    }
  }

  const byKind = (kind: AIAnalysisKind) => items.find((i) => i.kind === kind)
  const damage = items.filter((i) => i.kind === 'damage_assessment')

  if (loading) {
    return <p className="text-slate-500 text-center py-12">Cargando análisis IA...</p>
  }

  if (items.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center space-y-3">
          <Bot className="h-8 w-8 mx-auto text-slate-300" />
          <p className="text-slate-500 text-sm">
            Todavía no se ejecutaron análisis sobre este expediente.
            <br />
            Se disparan automáticamente al pasar a <strong>En evaluación</strong>.
          </p>
          {canRefresh && (
            <Button onClick={handleRefresh} disabled={refreshing} variant="outline" size="sm">
              <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
              Ejecutar análisis ahora
            </Button>
          )}
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {canRefresh && (
        <div className="flex justify-end">
          <Button onClick={handleRefresh} disabled={refreshing} variant="outline" size="sm">
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Re-ejecutar análisis
          </Button>
        </div>
      )}

      <AnalysisCard
        title="Inconsistencias detectadas"
        icon={<SearchCheck className="h-4 w-4" />}
        analysis={byKind('inconsistency')}
        render={(a) => <InconsistenciesList analysis={a} />}
      />
      <AnalysisCard
        title="Posibles duplicados"
        icon={<Copy className="h-4 w-4" />}
        analysis={byKind('duplicate')}
        render={(a) => <DuplicatesPanel analysis={a} />}
      />
      <AnalysisCard
        title="Riesgo de fraude"
        icon={<ShieldAlert className="h-4 w-4" />}
        analysis={byKind('fraud_score')}
        render={(a) => <FraudScoreCard analysis={a} />}
      />

      {/* CU-33: análisis de daño hechos por el asegurado desde la app (promovidos al formalizar) */}
      {damage.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Camera className="h-4 w-4" /> Análisis de daño por foto (app del asegurado)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {damage.map((d) => {
              const p = (d.payload ?? {}) as unknown as DamageAssessment
              return (
                <div key={d.id} className="flex items-center justify-between rounded-md border border-slate-200 p-3 text-sm">
                  <div>
                    <p className="font-medium text-slate-800">{p.damage_type ?? '—'}</p>
                    <p className="text-xs text-slate-500">{d.explanation}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="font-medium capitalize">{p.severity ?? '—'}</p>
                    {typeof p.confidence === 'number' && (
                      <p className="text-xs text-slate-400">confianza {(p.confidence * 100).toFixed(0)}%</p>
                    )}
                  </div>
                </div>
              )
            })}
          </CardContent>
        </Card>
      )}
    </div>
  )
}

function AnalysisCard({
  title,
  icon,
  analysis,
  render,
}: {
  title: string
  icon: React.ReactNode
  analysis: AIAnalysis | undefined
  render: (a: AIAnalysis) => React.ReactNode
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-base">
          <span className="flex items-center gap-2">{icon} {title}</span>
          {analysis && (
            <span className="text-xs font-normal text-slate-400">
              {new Date(analysis.created_at).toLocaleString()}
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {!analysis && <p className="text-sm text-slate-400">Sin resultados todavía.</p>}
        {analysis?.status === 'processing' && (
          <p className="flex items-center gap-2 text-sm text-slate-500">
            <Loader2 className="h-4 w-4 animate-spin" /> Calculando...
          </p>
        )}
        {analysis?.status === 'error' && (
          <p className="text-sm text-red-600 bg-red-50 rounded-md px-3 py-2">
            {analysis.explanation || 'El análisis falló.'}
          </p>
        )}
        {analysis?.status === 'done' && render(analysis)}
      </CardContent>
    </Card>
  )
}
