'use client'

import { useState } from 'react'
import { toast } from 'sonner'
import { claimsApi } from '@/lib/api/claims'
import { Button } from '@/components/ui/button'
import { Dialog } from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import type { Claim } from '@/types/claim'

interface Props {
  open: boolean
  onClose: () => void
  claimId: string
  onDecided: (claim: Claim) => void
}

export default function DecisionPanel({ open, onClose, claimId, onDecided }: Props) {
  const [decision, setDecision] = useState<'approved' | 'rejected' | ''>('')
  const [reason, setReason] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async () => {
    if (!decision || !reason) return
    setSubmitting(true)
    try {
      const claim = await claimsApi.decide(claimId, { decision: decision as 'approved' | 'rejected', reason })
      toast.success(`Expediente ${decision === 'approved' ? 'aprobado' : 'rechazado'}`)
      onDecided(claim)
      onClose()
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Error al decidir')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onClose={onClose} title="Decidir expediente">
      <div className="space-y-4">
        <div className="flex gap-3">
          <Button
            variant={decision === 'approved' ? 'default' : 'outline'}
            className={decision === 'approved' ? 'bg-green-600 hover:bg-green-700' : ''}
            onClick={() => setDecision('approved')}
          >
            Aprobar
          </Button>
          <Button
            variant={decision === 'rejected' ? 'default' : 'outline'}
            className={decision === 'rejected' ? 'bg-red-600 hover:bg-red-700' : ''}
            onClick={() => setDecision('rejected')}
          >
            Rechazar
          </Button>
        </div>
        <div className="space-y-2">
          <Label htmlFor="decision-reason">Motivo</Label>
          <Textarea id="decision-reason" value={reason} onChange={(e) => setReason(e.target.value)} rows={3} placeholder="Justificación de la decisión" required />
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="outline" onClick={onClose}>Cancelar</Button>
          <Button onClick={handleSubmit} disabled={!decision || !reason || submitting}>{submitting ? 'Procesando...' : 'Confirmar decisión'}</Button>
        </div>
      </div>
    </Dialog>
  )
}
