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
  currentAnalystId: string | null
  onAssigned: (claim: Claim) => void
}

export default function AssignAnalystDialog({ open, onClose, claimId, currentAnalystId, onAssigned }: Props) {
  const [analystId, setAnalystId] = useState('')
  const [reason, setReason] = useState('')
  const [analysts, setAnalysts] = useState<{ id: string; full_name: string }[]>([])
  const [loadingList, setLoadingList] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (!open) return
    setLoadingList(true)
    usersApi.listByRole(['analyst'])
      .then((items) => setAnalysts(
        items
          .filter((u) => u.id !== currentAnalystId)
          .map((u) => ({ id: u.id, full_name: u.full_name }))
      ))
      .catch(() => toast.error('Error al cargar analistas'))
      .finally(() => setLoadingList(false))
  }, [open, currentAnalystId])

  const handleSubmit = async () => {
    if (!analystId) return
    setSubmitting(true)
    try {
      const claim = await claimsApi.assignAnalyst(claimId, {
        analyst_user_id: analystId,
        reason: reason || undefined,
      })
      toast.success('Analista asignado')
      onAssigned(claim)
      onClose()
    } catch {
      toast.error('Error al asignar analista')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onClose={onClose} title="Asignar analista">
      <div className="space-y-4">
        <p className="text-sm text-slate-500">Seleccioná un analista del tenant.</p>
        <div className="space-y-2">
          <Label htmlFor="analyst-select">Analista</Label>
          <Select
            id="analyst-select"
            value={analystId}
            onChange={(e) => setAnalystId(e.target.value)}
            disabled={loadingList}
            options={[
              { value: '', label: loadingList ? 'Cargando...' : 'Seleccionar analista' },
              ...analysts.map((a) => ({ value: a.id, label: a.full_name })),
            ]}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="assign-reason">Motivo (opcional)</Label>
          <Textarea id="assign-reason" value={reason} onChange={(e) => setReason(e.target.value)} rows={2} placeholder="Ej: redistribución de carga" />
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="outline" onClick={onClose}>Cancelar</Button>
          <Button onClick={handleSubmit} disabled={!analystId || submitting}>{submitting ? 'Asignando...' : 'Asignar'}</Button>
        </div>
      </div>
    </Dialog>
  )
}
