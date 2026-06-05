'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Dialog } from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { claimRequestsApi } from '@/lib/api/claim-requests'
import { evidencesApi } from '@/lib/api/evidences'
import { policyholdersApi, type Policyholder } from '@/lib/api/policyholders'
import { policiesApi, type Policy } from '@/lib/api/policies'
import { vehiclesApi, type Vehicle } from '@/lib/api/vehicles'
import EvidenceUploader from '@/components/claims/EvidenceUploader'
import EvidenceGallery from '@/components/claims/EvidenceGallery'
import type { ClaimRequest } from '@/types/claim-request'
import type { FormalizeResponse } from '@/types/claim'
import type { Evidence } from '@/types/evidence'

// Formateadores: la API entrega fechas/horas crudas (ISO, HH:MM:SS).
function fmtDate(s: string | null | undefined): string | null {
  if (!s) return null
  const d = new Date(`${s}T00:00:00`)
  return isNaN(d.getTime()) ? s : d.toLocaleDateString('es', { day: '2-digit', month: 'long', year: 'numeric' })
}
function fmtTime(t: string | null | undefined): string | null {
  if (!t) return null
  return t.slice(0, 5) // "13:11:00" → "13:11"
}
function fmtDateTime(iso: string | null | undefined): string | null {
  if (!iso) return null
  const d = new Date(iso)
  return isNaN(d.getTime())
    ? iso
    : d.toLocaleString('es', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

const STATUS_MAP: Record<string, { label: string; color: string }> = {
  draft: { label: 'Borrador', color: 'bg-gray-100 text-gray-700' },
  submitted: { label: 'Enviada', color: 'bg-blue-100 text-blue-700' },
  under_intake_review: { label: 'En revisión', color: 'bg-yellow-100 text-yellow-700' },
  formalized: { label: 'Formalizada', color: 'bg-green-100 text-green-700' },
  rejected_at_intake: { label: 'Rechazada', color: 'bg-red-100 text-red-700' },
}

export default function ClaimRequestDetailPage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()
  const [request, setRequest] = useState<ClaimRequest | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionInProgress, setActionInProgress] = useState(false)
  const [rejectOpen, setRejectOpen] = useState(false)
  const [rejectReason, setRejectReason] = useState('')
  const [formalizedClaim, setFormalizedClaim] = useState<FormalizeResponse | null>(null)
  const [evidences, setEvidences] = useState<Evidence[]>([])
  const [eviLoading, setEviLoading] = useState(false)
  const [policyholder, setPolicyholder] = useState<Policyholder | null>(null)
  const [policy, setPolicy] = useState<Policy | null>(null)
  const [vehicle, setVehicle] = useState<Vehicle | null>(null)

  useEffect(() => {
    let active = true
    claimRequestsApi
      .get(id)
      .then((req) => {
        if (!active) return
        setRequest(req)
        // Traer las entidades relacionadas para mostrar nombres en vez de IDs.
        policyholdersApi.get(req.policyholder_id).then((p) => active && setPolicyholder(p)).catch(() => {})
        policiesApi.get(req.policy_id).then((p) => active && setPolicy(p)).catch(() => {})
        vehiclesApi.get(req.vehicle_id).then((v) => active && setVehicle(v)).catch(() => {})
      })
      .catch(() => setError('No se pudo cargar la solicitud'))
      .finally(() => active && setLoading(false))
    setEviLoading(true)
    evidencesApi.listForRequest(id).then((r) => active && setEvidences(r.items)).catch(() => {}).finally(() => active && setEviLoading(false))
    return () => {
      active = false
    }
  }, [id])

  const handleTake = async () => {
    setActionInProgress(true)
    try {
      const updated = await claimRequestsApi.take(id)
      setRequest(updated)
      toast.success('Solicitud tomada')
    } catch { toast.error('Error al tomar la solicitud') }
    finally { setActionInProgress(false) }
  }

  const handleRelease = async () => {
    setActionInProgress(true)
    try {
      const updated = await claimRequestsApi.release(id)
      setRequest(updated)
      toast.success('Solicitud liberada')
    } catch { toast.error('Error al liberar la solicitud') }
    finally { setActionInProgress(false) }
  }

  const handleFormalize = async () => {
    setActionInProgress(true)
    try {
      const result = await claimRequestsApi.formalize(id)
      setRequest(result.request ?? request)
      setFormalizedClaim(result)
      toast.success('Expediente formalizado')
    } catch { toast.error('Error al formalizar') }
    finally { setActionInProgress(false) }
  }

  const handleReject = async () => {
    if (!rejectReason.trim()) return
    setActionInProgress(true)
    try {
      const updated = await claimRequestsApi.reject(id, { reason: rejectReason.trim() })
      setRequest(updated)
      setRejectOpen(false)
      toast.success('Solicitud rechazada')
    } catch { toast.error('Error al rechazar') }
    finally { setActionInProgress(false) }
  }

  if (loading) {
    return <div className="flex items-center justify-center py-16 text-slate-500">Cargando...</div>
  }

  if (error || !request) {
    return <div className="flex items-center justify-center py-16 text-red-600">{error || 'No encontrada'}</div>
  }

  const statusInfo = STATUS_MAP[request.status] || { label: request.status, color: 'bg-gray-100 text-gray-700' }
  const coords =
    request.accident_lat != null && request.accident_lng != null
      ? `${Number(request.accident_lat).toFixed(6)}, ${Number(request.accident_lng).toFixed(6)}`
      : null

  const fields: [string, string | null][] = [
    ['Número de solicitud', request.request_number],
    ['Asegurado', policyholder ? `${policyholder.full_name} · ${policyholder.document_id}` : null],
    ['Póliza', policy ? `${policy.policy_number} · ${policy.coverage_type}` : null],
    ['Vehículo', vehicle ? `${vehicle.make} ${vehicle.model} (${vehicle.year}) · ${vehicle.plate}` : null],
    ['Fecha del accidente', fmtDate(request.accident_date)],
    ['Hora del accidente', fmtTime(request.accident_time)],
    ['Ubicación', request.accident_location],
    ['Coordenadas GPS', coords],
    ['Descripción', request.accident_description],
    ['Daños reportados', request.reported_damages],
    ['Enviada', fmtDateTime(request.submitted_at)],
  ]

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Solicitud</h1>
        <Button variant="outline" size="sm" onClick={() => router.push('/dashboard/solicitudes')}>
          ← Volver
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <CardTitle>{request.request_number || `Solicitud ${id.slice(0, 8)}`}</CardTitle>
            <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${statusInfo.color}`}>
              {statusInfo.label}
            </span>
          </div>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-2 gap-4 text-sm">
            {fields.filter(([, v]) => v).map(([label, value]) => (
              <div key={label}>
                <dt className="text-slate-500">{label}</dt>
                <dd className="text-slate-900">{value}</dd>
              </div>
            ))}
          </dl>
        </CardContent>
      </Card>

      {request.status !== 'formalized' && request.status !== 'rejected_at_intake' && (
        <Card>
          <CardHeader><CardTitle>Evidencias</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <EvidenceUploader subjectType="claim_request" subjectId={id} onUploaded={(ev) => setEvidences((p) => [ev, ...p])} />
            <EvidenceGallery items={evidences} loading={eviLoading} />
          </CardContent>
        </Card>
      )}

      {formalizedClaim && (
        <Card className="border-green-300 bg-green-50">
          <CardContent className="p-4 text-sm">
            <p className="font-medium text-green-800">Expediente creado exitosamente</p>
            <p className="text-green-700">
              Número: {formalizedClaim.claim.claim_number}
            </p>
            <Button
              variant="link"
              size="sm"
              className="p-0 h-auto text-green-700"
              onClick={() => router.push(`/dashboard/expedientes/${formalizedClaim.claim.id}`)}
            >
              Ver expediente →
            </Button>
          </CardContent>
        </Card>
      )}

      {request.status === 'rejected_at_intake' && request.intake_decision_reason && (
        <Card className="border-red-300 bg-red-50">
          <CardHeader><CardTitle className="text-red-800 text-base">Motivo del rechazo</CardTitle></CardHeader>
          <CardContent><p className="text-sm text-red-700">{request.intake_decision_reason}</p></CardContent>
        </Card>
      )}

      {request.status === 'formalized' && request.formalized_claim_id && (
        <Card>
          <CardContent className="p-4 text-sm flex items-center justify-between">
            <span className="text-slate-600">Esta solicitud ya fue formalizada</span>
            <Button
              size="sm"
              variant="outline"
              onClick={() => router.push(`/dashboard/expedientes/${request.formalized_claim_id}`)}
            >
              Ver expediente →
            </Button>
          </CardContent>
        </Card>
      )}

      <div className="flex gap-3">
        {request.status === 'submitted' && (
          <Button onClick={handleTake} disabled={actionInProgress}>
            {actionInProgress ? '...' : 'Tomar'}
          </Button>
        )}
        {request.status === 'under_intake_review' && (
          <>
            <Button onClick={handleFormalize} disabled={actionInProgress} variant="default">
              {actionInProgress ? '...' : 'Formalizar'}
            </Button>
            <Button onClick={() => setRejectOpen(true)} disabled={actionInProgress} variant="destructive">
              Rechazar
            </Button>
            <Button onClick={handleRelease} disabled={actionInProgress} variant="outline">
              Liberar
            </Button>
          </>
        )}
      </div>

      <Dialog open={rejectOpen} onClose={() => setRejectOpen(false)} title="Rechazar solicitud">
        <div className="space-y-4">
          <p className="text-sm text-slate-600">Indica el motivo del rechazo</p>
          <Textarea
            placeholder="Motivo del rechazo..."
            rows={4}
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
          />
          <div className="flex justify-end gap-3">
            <Button variant="outline" onClick={() => setRejectOpen(false)}>Cancelar</Button>
            <Button variant="destructive" onClick={handleReject} disabled={actionInProgress || !rejectReason.trim()}>
              {actionInProgress ? '...' : 'Rechazar'}
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  )
}
