'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { toast } from 'sonner'
import { claimsApi } from '@/lib/api/claims'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'

export default function NuevoExpedientePage() {
  const router = useRouter()
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setSubmitting(true)
    const form = new FormData(e.currentTarget)

    const data = {
      policyholder_id: form.get('policyholder_id') as string,
      policy_id: form.get('policy_id') as string,
      vehicle_id: form.get('vehicle_id') as string,
      accident_date: form.get('accident_date') as string,
      accident_time: (form.get('accident_time') as string) || undefined,
      accident_location: form.get('accident_location') as string,
      accident_description: (form.get('accident_description') as string) || undefined,
      reported_damages: (form.get('reported_damages') as string) || undefined,
    }

    try {
      const claim = await claimsApi.create(data)
      toast.success(`Expediente creado: ${claim.claim_number}`)
      router.push('/dashboard/expedientes')
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al crear el expediente'
      toast.error(msg)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="mx-auto max-w-xl py-8">
      <Card>
        <CardHeader>
          <CardTitle>Nuevo expediente</CardTitle>
          <CardDescription>Crear un expediente directo sin solicitud previa.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="policyholder_id">ID Asegurado *</Label>
                <Input id="policyholder_id" name="policyholder_id" required placeholder="UUID del asegurado" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="policy_id">ID Póliza *</Label>
                <Input id="policy_id" name="policy_id" required placeholder="UUID de la póliza" />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="vehicle_id">ID Vehículo *</Label>
              <Input id="vehicle_id" name="vehicle_id" required placeholder="UUID del vehículo" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="accident_date">Fecha del accidente *</Label>
                <Input id="accident_date" name="accident_date" type="date" required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="accident_time">Hora del accidente</Label>
                <Input id="accident_time" name="accident_time" type="time" />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="accident_location">Ubicación *</Label>
              <Input id="accident_location" name="accident_location" required placeholder="Dirección o lugar del accidente" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="accident_description">Descripción</Label>
              <Textarea id="accident_description" name="accident_description" rows={3} placeholder="Describa cómo ocurrió el accidente" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="reported_damages">Daños reportados</Label>
              <Textarea id="reported_damages" name="reported_damages" rows={2} placeholder="Describa los daños visibles" />
            </div>
            <div className="flex justify-end gap-3 pt-2">
              <Button type="button" variant="outline" onClick={() => router.back()}>
                Cancelar
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting ? 'Creando...' : 'Crear expediente'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
