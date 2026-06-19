'use client'

import { useState, useEffect } from 'react'
import { toast } from 'sonner'
import { claimsApi } from '@/lib/api/claims'
import { usersApi } from '@/lib/api/users'
import { Button } from '@/components/ui/button'
import { Dialog } from '@/components/ui/dialog'
import { Select } from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import type { Claim } from '@/types/claim'

interface Props {
  open: boolean
  onClose: () => void
  claimId: string
  onEscalated: (claim: Claim) => void
}

export default function EscalateDialog({ open, onClose, claimId, onEscalated }: Props) {
  const [supervisorId, setSupervisorId] = useState('')
  const [reason, setReason] = useState('')
  const [supervisors, setSupervisors] = useState<{ id: string; full_name: string }[]>([])
  const [loadingList, setLoadingList] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (!open) return
    setLoadingList(true)
    usersApi.listByRole(['supervisor', 'admin'])
      .then((items) => setSupervisors(items.map((u) => ({ id: u.id, full_name: u.full_name }))))
      .catch(() => toast.error('Error al cargar supervisores'))
      .finally(() => setLoadingList(false))
  }, [open])

  const handleSubmit = async () => {
    if (!supervisorId || !reason) return
    setSubmitting(true)
    try {
      const claim = await claimsApi.escalate(claimId, { supervisor_user_id: supervisorId, reason })
      toast.success('Expediente escalado')
      onEscalated(claim)
      onClose()
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      toast.error(detail || 'Error al escalar')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onClose={onClose} title="Escalar expediente">
      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="supervisor-select">Supervisor</Label>
          <Select
            id="supervisor-select"
            value={supervisorId}
            onChange={(e) => setSupervisorId(e.target.value)}
            disabled={loadingList}
            options={[
              { value: '', label: loadingList ? 'Cargando...' : 'Seleccionar supervisor' },
              ...supervisors.map((s) => ({ value: s.id, label: s.full_name })),
            ]}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="escalate-reason">Motivo</Label>
          <Textarea id="escalate-reason" value={reason} onChange={(e) => setReason(e.target.value)} rows={3} placeholder="Por qué requiere revisión del supervisor" required />
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="outline" onClick={onClose}>Cancelar</Button>
          <Button onClick={handleSubmit} disabled={!supervisorId || !reason || submitting}>{submitting ? 'Escalando...' : 'Escalar'}</Button>
        </div>
      </div>
    </Dialog>
  )
}
