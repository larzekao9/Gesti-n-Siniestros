'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { toast } from 'sonner'
import { ArrowLeft } from 'lucide-react'
import { claimsApi } from '@/lib/api/claims'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Dialog } from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { Select } from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import type { Claim } from '@/types/claim'
import type { Observation } from '@/types/observation'
import type { ThirdParty } from '@/types/third-party'

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

const TRANSITIONS: Record<string, string[]> = {
  registered: ['in_review'],
  in_review: ['observed', 'in_evaluation'],
  observed: ['in_review', 'in_evaluation'],
  in_evaluation: ['approved', 'rejected'],
  approved: ['closed'],
  rejected: ['closed'],
}

const TP_KINDS = [
  { value: '', label: 'Seleccionar tipo' },
  { value: 'driver', label: 'Conductor' },
  { value: 'witness', label: 'Testigo' },
  { value: 'victim', label: 'Víctima' },
  { value: 'vehicle_owner', label: 'Propietario vehículo' },
]

const TP_KIND_LABELS: Record<string, string> = Object.fromEntries(
  TP_KINDS.slice(1).map((k) => [k.value, k.label])
)

const EMPTY_TP = { kind: '', full_name: '', document_id: '', contact_phone: '', vehicle_plate: '', vehicle_info: '', statement: '' }

export default function ExpedienteDetailPage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()
  const [claim, setClaim] = useState<Claim | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState(0)
  const [statusOpen, setStatusOpen] = useState(false)
  const [newStatus, setNewStatus] = useState('')
  const [statusReason, setStatusReason] = useState('')
  const [statusSubmitting, setStatusSubmitting] = useState(false)
  const [observations, setObservations] = useState<Observation[]>([])
  const [obsLoading, setObsLoading] = useState(false)
  const [comment, setComment] = useState('')
  const [isInternal, setIsInternal] = useState(false)
  const [obsSubmitting, setObsSubmitting] = useState(false)
  const [thirdParties, setThirdParties] = useState<ThirdParty[]>([])
  const [tpLoading, setTpLoading] = useState(false)
  const [tpForm, setTpForm] = useState({ ...EMPTY_TP })
  const [editingTpId, setEditingTpId] = useState<string | null>(null)
  const [tpSubmitting, setTpSubmitting] = useState(false)

  useEffect(() => { claimsApi.get(id).then(setClaim).catch(() => setError('No se pudo cargar el expediente')).finally(() => setLoading(false)) }, [id])

  useEffect(() => {
    if (activeTab === 1 && observations.length === 0) { setObsLoading(true); claimsApi.listObservations(id).then((r) => setObservations(r.items)).catch(() => toast.error('Error al cargar observaciones')).finally(() => setObsLoading(false)) }
    if (activeTab === 2 && thirdParties.length === 0) { setTpLoading(true); claimsApi.listThirdParties(id).then((r) => setThirdParties(r.items)).catch(() => toast.error('Error al cargar terceros')).finally(() => setTpLoading(false)) }
  }, [activeTab])

  const handleStatusChange = async () => {
    if (!newStatus) return
    setStatusSubmitting(true)
    try {
      const updated = await claimsApi.updateStatus(id, { new_status: newStatus, reason: statusReason || undefined })
      setClaim(updated)
      toast.success('Estado actualizado')
      setStatusOpen(false)
      setNewStatus('')
      setStatusReason('')
    } catch { toast.error('Error al cambiar estado') }
    finally { setStatusSubmitting(false) }
  }

  const handleCreateObservation = async () => {
    if (!comment.trim()) return
    setObsSubmitting(true)
    try {
      const obs = await claimsApi.createObservation(id, { comment: comment.trim(), is_internal: isInternal })
      setObservations((p) => [obs, ...p])
      setComment('')
      setIsInternal(false)
      toast.success('Observación agregada')
    } catch { toast.error('Error al crear observación') }
    finally { setObsSubmitting(false) }
  }

  const handleSaveTp = async () => {
    if (!tpForm.kind || !tpForm.full_name.trim()) return
    setTpSubmitting(true)
    try {
      const payload = {
        kind: tpForm.kind,
        full_name: tpForm.full_name.trim(),
        document_id: tpForm.document_id || undefined,
        contact_phone: tpForm.contact_phone || undefined,
        vehicle_plate: tpForm.vehicle_plate || undefined,
        vehicle_info: tpForm.vehicle_info || undefined,
        statement: tpForm.statement || undefined,
      }
      if (editingTpId) {
        const updated = await claimsApi.updateThirdParty(id, editingTpId, payload)
        setThirdParties((p) => p.map((t) => (t.id === editingTpId ? updated : t)))
        toast.success('Tercero actualizado')
      } else {
        const created = await claimsApi.createThirdParty(id, payload)
        setThirdParties((p) => [...p, created])
        toast.success('Tercero registrado')
      }
      setTpForm({ ...EMPTY_TP })
      setEditingTpId(null)
    } catch { toast.error('Error al guardar tercero') }
    finally { setTpSubmitting(false) }
  }

  const handleDeleteTp = async (tpId: string) => {
    if (!window.confirm('¿Eliminar este tercero?')) return
    try {
      await claimsApi.deleteThirdParty(id, tpId)
      setThirdParties((p) => p.filter((t) => t.id !== tpId))
      if (editingTpId === tpId) { setTpForm({ ...EMPTY_TP }); setEditingTpId(null) }
      toast.success('Tercero eliminado')
    } catch { toast.error('Error al eliminar tercero') }
  }

  const editTp = (tp: ThirdParty) => {
    setEditingTpId(tp.id)
    setTpForm({ kind: tp.kind, full_name: tp.full_name, document_id: tp.document_id || '', contact_phone: tp.contact_phone || '', vehicle_plate: tp.vehicle_plate || '', vehicle_info: tp.vehicle_info || '', statement: tp.statement || '' })
  }

  if (loading) return <div className="flex items-center justify-center py-40"><p className="text-slate-500">Cargando expediente...</p></div>
  if (error || !claim) return <div className="flex flex-col items-center justify-center py-40 gap-4"><p className="text-red-600">{error || 'Expediente no encontrado'}</p><Button variant="outline" onClick={() => router.push('/dashboard/expedientes')}>Volver a expedientes</Button></div>

  const status = STATUS_MAP[claim.status] || { label: claim.status, color: 'bg-gray-100 text-gray-700' }
  const allowed = TRANSITIONS[claim.status] || []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.push('/dashboard/expedientes')}><ArrowLeft className="h-5 w-5" /></Button>
          <div>
            <h1 className="text-2xl font-bold">{claim.claim_number}</h1>
            <p className="text-sm text-slate-500">Fuente: {claim.source === 'mobile_app' ? 'App móvil' : 'Interno'}</p>
          </div>
          <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-semibold ${status.color}`}>{status.label}</span>
        </div>
        {allowed.length > 0 && <Button onClick={() => setStatusOpen(true)}>Cambiar Estado</Button>}
      </div>
      <div className="flex border-b border-slate-200">
        {['Resumen', 'Observaciones', 'Terceros'].map((tab, i) => (
          <button key={tab} onClick={() => setActiveTab(i)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors -mb-px ${activeTab === i ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}>
            {tab}
          </button>
        ))}
      </div>
      {activeTab === 0 && (
        <Card>
          <CardHeader><CardTitle>Datos del expediente</CardTitle></CardHeader>
          <CardContent className="grid grid-cols-2 gap-4">
            <Field label="Fecha de accidente" value={claim.accident_date} />
            <Field label="Hora" value={claim.accident_time || '—'} />
            <Field label="Ubicación" value={claim.accident_location} />
            <Field label="Coordenadas" value={claim.accident_lat ? `${claim.accident_lat}, ${claim.accident_lng}` : '—'} />
            <Field label="Descripción" value={claim.accident_description || '—'} span />
            <Field label="Daños reportados" value={claim.reported_damages || '—'} span />
            <Field
              label="Asegurado"
              value={claim.policyholder ? `${claim.policyholder.full_name} (Doc: ${claim.policyholder.document_id})` : claim.policyholder_id}
            />
            <Field
              label="Póliza"
              value={claim.policy ? `${claim.policy.policy_number} · ${claim.policy.coverage_type} (vig. ${claim.policy.valid_from} → ${claim.policy.valid_to})` : claim.policy_id}
            />
            <Field
              label="Vehículo"
              value={claim.vehicle ? `${claim.vehicle.plate} · ${claim.vehicle.make} ${claim.vehicle.model} (${claim.vehicle.year})` : claim.vehicle_id}
              span
            />
            {claim.decision && <><Field label="Decisión" value={claim.decision === 'approved' ? 'Aprobado' : 'Rechazado'} /><Field label="Motivo" value={claim.decision_reason || '—'} /></>}
          </CardContent>
        </Card>
      )}
      {activeTab === 1 && (
        <div className="space-y-6">
          <Card>
            <CardHeader><CardTitle>Nueva observación</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>Comentario</Label>
                <Textarea value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Escriba la observación..." rows={3} />
              </div>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={isInternal} onChange={(e) => setIsInternal(e.target.checked)} className="rounded border-slate-300" />
                Solo visible internamente
              </label>
              <Button onClick={handleCreateObservation} disabled={obsSubmitting || !comment.trim()}>
                {obsSubmitting ? 'Guardando...' : 'Agregar observación'}
              </Button>
            </CardContent>
          </Card>
          {obsLoading ? <p className="text-slate-500 text-center py-8">Cargando...</p> : observations.length === 0 ? <p className="text-slate-400 text-center py-8">Sin observaciones</p> : (
            <div className="space-y-3">
              {observations.map((obs) => (
                <Card key={obs.id}>
                  <CardContent className="pt-4">
                    <p className="text-sm whitespace-pre-wrap">{obs.comment}</p>
                    <div className="flex gap-3 mt-2 text-xs text-slate-400">
                      <span>{new Date(obs.created_at).toLocaleString()}</span>
                      {obs.is_internal && <span className="text-yellow-600 font-medium">Interno</span>}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}
      {activeTab === 2 && (
        <div className="space-y-6">
          <Card>
            <CardHeader><CardTitle>{editingTpId ? 'Editar tercero' : 'Agregar tercero'}</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div><Label>Tipo *</Label><Select options={TP_KINDS} value={tpForm.kind} onChange={(e) => setTpForm({ ...tpForm, kind: e.target.value })} /></div>
                <div><Label>Nombre completo *</Label><Input value={tpForm.full_name} onChange={(e) => setTpForm({ ...tpForm, full_name: e.target.value })} placeholder="Nombre del tercero" /></div>
                <div><Label>Documento ID</Label><Input value={tpForm.document_id} onChange={(e) => setTpForm({ ...tpForm, document_id: e.target.value })} placeholder="CI / NIT" /></div>
                <div><Label>Teléfono</Label><Input value={tpForm.contact_phone} onChange={(e) => setTpForm({ ...tpForm, contact_phone: e.target.value })} placeholder="+591..." /></div>
                <div><Label>Placa vehículo</Label><Input value={tpForm.vehicle_plate} onChange={(e) => setTpForm({ ...tpForm, vehicle_plate: e.target.value })} placeholder="ABC-1234" /></div>
                <div><Label>Info vehículo</Label><Input value={tpForm.vehicle_info} onChange={(e) => setTpForm({ ...tpForm, vehicle_info: e.target.value })} placeholder="Marca, modelo, color..." /></div>
              </div>
              <div><Label>Declaración</Label><Textarea value={tpForm.statement} onChange={(e) => setTpForm({ ...tpForm, statement: e.target.value })} placeholder="Declaración del tercero..." rows={3} /></div>
              <div className="flex gap-2">
                <Button onClick={handleSaveTp} disabled={tpSubmitting || !tpForm.kind || !tpForm.full_name.trim()}>{tpSubmitting ? 'Guardando...' : editingTpId ? 'Actualizar' : 'Agregar'}</Button>
                {editingTpId && <Button variant="ghost" onClick={() => { setTpForm({ ...EMPTY_TP }); setEditingTpId(null) }}>Cancelar</Button>}
              </div>
            </CardContent>
          </Card>
          {tpLoading ? <p className="text-slate-500 text-center py-8">Cargando...</p> : thirdParties.length === 0 ? <p className="text-slate-400 text-center py-8">Sin terceros registrados</p> : (
            <div className="space-y-3">
              {thirdParties.map((tp) => (
                <Card key={tp.id}>
                  <CardContent className="pt-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{tp.full_name}</span>
                          <span className="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-600">{TP_KIND_LABELS[tp.kind] || tp.kind}</span>
                        </div>
                        <div className="text-sm text-slate-500 mt-1 space-y-0.5">
                          {tp.document_id && <p>Doc: {tp.document_id}</p>}
                          {tp.contact_phone && <p>Tel: {tp.contact_phone}</p>}
                          {tp.vehicle_plate && <p>Placa: {tp.vehicle_plate}</p>}
                          {tp.vehicle_info && <p>Vehículo: {tp.vehicle_info}</p>}
                          {tp.statement && <p className="italic mt-1">&ldquo;{tp.statement}&rdquo;</p>}
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button size="sm" variant="outline" onClick={() => editTp(tp)}>Editar</Button>
                        <Button size="sm" variant="destructive" onClick={() => handleDeleteTp(tp.id)}>Eliminar</Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      <Dialog open={statusOpen} onClose={() => setStatusOpen(false)} title="Cambiar estado">
        <div className="space-y-4">
          <div><Label>Estado actual</Label><p className="text-sm font-medium mt-1">{status.label}</p></div>
          <div><Label>Nuevo estado</Label><Select options={[{ value: '', label: 'Seleccionar estado' }, ...allowed.map((s) => ({ value: s, label: STATUS_MAP[s]?.label || s }))]} value={newStatus} onChange={(e) => setNewStatus(e.target.value)} /></div>
          <div><Label>Motivo (opcional)</Label><Textarea value={statusReason} onChange={(e) => setStatusReason(e.target.value)} placeholder="Motivo del cambio de estado..." rows={3} /></div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => setStatusOpen(false)}>Cancelar</Button>
            <Button onClick={handleStatusChange} disabled={statusSubmitting || !newStatus}>{statusSubmitting ? 'Guardando...' : 'Confirmar cambio'}</Button>
          </div>
        </div>
      </Dialog>
    </div>
  )
}

function Field({ label, value, span }: { label: string; value: string; span?: boolean }) {
  return <div className={span ? 'col-span-2' : ''}><Label>{label}</Label><p className="text-sm mt-1 text-slate-700 break-words">{value}</p></div>
}
