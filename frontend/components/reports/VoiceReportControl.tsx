'use client'

import { useRef, useState } from 'react'
import { Mic, Square, Loader2, AlertTriangle, Check, Sparkles } from 'lucide-react'
import { toast } from 'sonner'

import { reportsApi } from '@/lib/api/reports'
import type { ReportFilters, VoiceReportInterpretation } from '@/types/report'
import { Button } from '@/components/ui/button'

interface Props {
  /** Aplica los filtros interpretados al formulario (paso de confirmación). */
  onApply: (filters: ReportFilters, interpretation: VoiceReportInterpretation) => void
}

type Phase = 'idle' | 'recording' | 'processing'

export default function VoiceReportControl({ onApply }: Props) {
  const [phase, setPhase] = useState<Phase>('idle')
  const [result, setResult] = useState<VoiceReportInterpretation | null>(null)
  const recorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])

  const startRecording = async () => {
    if (typeof navigator === 'undefined' || !navigator.mediaDevices?.getUserMedia) {
      toast.error('Tu navegador no soporta grabación de audio')
      return
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)
      chunksRef.current = []
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }
      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop())
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || 'audio/webm' })
        await sendAudio(blob)
      }
      recorderRef.current = recorder
      recorder.start()
      setResult(null)
      setPhase('recording')
    } catch {
      toast.error('No se pudo acceder al micrófono. Revisá los permisos.')
    }
  }

  const stopRecording = () => {
    recorderRef.current?.stop()
    setPhase('processing')
  }

  const sendAudio = async (blob: Blob) => {
    try {
      const interpretation = await reportsApi.interpretVoice(blob)
      setResult(interpretation)
      if (!interpretation.supported) {
        toast.warning('Ese reporte no está disponible')
      }
    } catch {
      toast.error('No se pudo interpretar el audio')
      setResult(null)
    } finally {
      setPhase('idle')
    }
  }

  const applyResult = () => {
    if (!result) return
    const f = result.filters
    onApply(
      {
        format: f.format,
        from: f.from ?? undefined,
        to: f.to ?? undefined,
        status: f.status ?? undefined,
        analyst: f.analyst ?? undefined,
        supervisor: f.supervisor ?? undefined,
        policyholder: f.policyholder ?? undefined,
        q: f.q ?? undefined,
      },
      result
    )
    toast.success('Filtros aplicados desde tu pedido por voz')
    setResult(null)
  }

  return (
    <div className="rounded-xl border border-indigo-200 bg-indigo-50/60 p-5 shadow-sm">
      <div className="flex items-start gap-3">
        <Sparkles className="mt-0.5 h-5 w-5 shrink-0 text-indigo-600" />
        <div className="flex-1">
          <h2 className="text-sm font-semibold text-indigo-900">
            Pedí el reporte por voz
          </h2>
          <p className="mt-0.5 text-xs text-indigo-700/80">
            Ej.: «Generá en Excel los siniestros aprobados de junio» o «los expedientes
            del analista Juan Pérez de este mes».
          </p>

          <div className="mt-3">
            {phase === 'recording' ? (
              <Button onClick={stopRecording} variant="destructive">
                <Square className="mr-2 h-4 w-4" />
                Detener y enviar
                <span className="ml-2 inline-flex h-2 w-2 animate-pulse rounded-full bg-white" />
              </Button>
            ) : phase === 'processing' ? (
              <Button disabled>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Interpretando…
              </Button>
            ) : (
              <Button onClick={startRecording}>
                <Mic className="mr-2 h-4 w-4" />
                Grabar pedido
              </Button>
            )}
          </div>
        </div>
      </div>

      {result && (
        <div className="mt-4 rounded-lg border border-indigo-200 bg-white p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
            Lo que entendí
          </p>
          <p className="mt-1 text-sm italic text-slate-600">“{result.transcript}”</p>

          {result.supported ? (
            <>
              <ul className="mt-3 space-y-1 text-sm text-slate-700">
                <li>
                  <span className="text-slate-400">Formato:</span>{' '}
                  {result.resolved.format.toUpperCase()}
                </li>
                {result.resolved.status_label && (
                  <li>
                    <span className="text-slate-400">Estado:</span>{' '}
                    {result.resolved.status_label}
                  </li>
                )}
                {(result.filters.from || result.filters.to) && (
                  <li>
                    <span className="text-slate-400">Rango:</span>{' '}
                    {result.filters.from ?? '…'} → {result.filters.to ?? '…'}
                  </li>
                )}
                {result.resolved.analyst_label && (
                  <li>
                    <span className="text-slate-400">Analista:</span>{' '}
                    {result.resolved.analyst_label}
                  </li>
                )}
                {result.resolved.supervisor_label && (
                  <li>
                    <span className="text-slate-400">Supervisor:</span>{' '}
                    {result.resolved.supervisor_label}
                  </li>
                )}
                {result.resolved.policyholder_label && (
                  <li>
                    <span className="text-slate-400">Asegurado:</span>{' '}
                    {result.resolved.policyholder_label}
                  </li>
                )}
                {result.filters.q && (
                  <li>
                    <span className="text-slate-400">Búsqueda:</span> {result.filters.q}
                  </li>
                )}
              </ul>

              {result.warnings.length > 0 && (
                <div className="mt-3 flex items-start gap-2 rounded-md bg-amber-50 p-2 text-xs text-amber-800">
                  <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                  <ul className="space-y-0.5">
                    {result.warnings.map((w, i) => (
                      <li key={i}>{w}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="mt-4 flex gap-2">
                <Button size="sm" onClick={applyResult}>
                  <Check className="mr-2 h-4 w-4" />
                  Aplicar filtros
                </Button>
                <Button size="sm" variant="outline" onClick={() => setResult(null)}>
                  Descartar
                </Button>
              </div>
            </>
          ) : (
            <div className="mt-3 flex items-start gap-2 rounded-md bg-amber-50 p-3 text-sm text-amber-800">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{result.note || 'Ese reporte no está disponible.'}</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
