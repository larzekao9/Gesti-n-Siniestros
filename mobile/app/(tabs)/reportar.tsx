import { useState } from 'react'
import { ScrollView, Text, View } from 'react-native'
import { useRouter } from 'expo-router'
import { Car, ShieldCheck } from 'lucide-react-native'

import { Button } from '@/components/ui/Button'
import { EmptyState } from '@/components/ui/EmptyState'
import { Loading } from '@/components/ui/Loading'
import { OptionPicker, type Option } from '@/components/ui/OptionPicker'
import { Screen } from '@/components/ui/Screen'
import { WizardStepper } from '@/components/claim-requests/WizardStepper'
import { apiErrorMessage } from '@/lib/api/client'
import { useMyPolicies, useMyVehicles } from '@/lib/hooks/useCatalog'
import { useCreateDraft } from '@/lib/hooks/useDraft'
import { useAuthStore } from '@/lib/stores/authStore'
import { colors } from '@/lib/theme'

// CU-02 (paso 1): selección de vehículo + póliza. Al continuar se crea el draft.
export default function ReportarScreen() {
  const router = useRouter()
  const account = useAuthStore((s) => s.account)
  const vehicles = useMyVehicles()
  const policies = useMyPolicies()
  const createDraft = useCreateDraft()

  const [vehicleId, setVehicleId] = useState<string | null>(null)
  const [policyId, setPolicyId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  if (vehicles.isLoading || policies.isLoading) {
    return <Loading label="Cargando tus vehículos…" />
  }

  const vehList = vehicles.data ?? []
  const polList = policies.data ?? []

  if (vehList.length === 0) {
    return (
      <Screen edges={['top']}>
        <View className="px-5 pt-3">
          <Text className="text-2xl font-bold text-brand">Reportar siniestro</Text>
        </View>
        <EmptyState
          icon={Car}
          title="No encontramos vehículos a tu nombre"
          description="Tu aseguradora debe registrar tu póliza y vehículo antes de que puedas reportar un siniestro. Contactá a tu asesor."
        />
      </Screen>
    )
  }

  const vehicleOptions: Option[] = vehList.map((v) => ({
    value: v.id,
    label: `${v.make} ${v.model} ${v.year}`,
    sublabel: `Placa ${v.plate}`,
  }))

  // Sugerir la póliza del vehículo elegido por defecto.
  const selectedVehicle = vehList.find((v) => v.id === vehicleId)
  const policyOptions: Option[] = polList.map((p) => ({
    value: p.id,
    label: p.policy_number,
    sublabel: `${p.coverage_type} · vence ${p.valid_to}`,
  }))

  function onSelectVehicle(id: string) {
    setVehicleId(id)
    const v = vehList.find((x) => x.id === id)
    if (v && !policyId) setPolicyId(v.policy_id)
  }

  async function onContinue() {
    if (!vehicleId || !policyId || !account) {
      setError('Elegí el vehículo y la póliza para continuar')
      return
    }
    setError(null)
    try {
      const draft = await createDraft.mutateAsync({
        policyholder_id: account.policyholder_id,
        policy_id: policyId,
        vehicle_id: vehicleId,
      })
      router.push(`/reportar/${draft.id}/accidente`)
      // Reset para el próximo reporte.
      setVehicleId(null)
      setPolicyId(null)
    } catch (err) {
      setError(apiErrorMessage(err, 'No se pudo iniciar el reporte'))
    }
  }

  return (
    <Screen edges={['top']}>
      <ScrollView contentContainerStyle={{ padding: 20, gap: 4 }}>
        <Text className="text-2xl font-bold text-brand">Reportar siniestro</Text>
        <Text className="text-sm text-muted">Empecemos por tu vehículo.</Text>

        <WizardStepper current={0} />

        <View className="mt-2 flex-row items-start gap-2 rounded-xl bg-info-50 p-3">
          <ShieldCheck size={18} color={colors.info} />
          <Text className="flex-1 text-xs leading-4 text-info">
            Tu reporte se guarda automáticamente. Podés retomarlo cuando quieras desde
            "Mis reclamos".
          </Text>
        </View>

        <View className="mt-4 gap-4">
          <OptionPicker
            label="Vehículo del siniestro"
            placeholder="Elegí tu vehículo"
            options={vehicleOptions}
            value={vehicleId}
            onChange={onSelectVehicle}
            required
          />
          <OptionPicker
            label="Póliza"
            placeholder="Elegí la póliza"
            options={policyOptions}
            value={policyId}
            onChange={setPolicyId}
            required
            emptyHint="No tenés pólizas activas"
          />
        </View>

        {selectedVehicle ? (
          <View className="mt-3 rounded-xl border border-line bg-white p-4">
            <View className="flex-row items-center gap-2">
              <Car size={18} color={colors.brand} />
              <Text className="font-semibold text-brand">
                {selectedVehicle.make} {selectedVehicle.model}
              </Text>
            </View>
            <Text className="mt-1 text-xs text-muted">
              Placa {selectedVehicle.plate} · {selectedVehicle.year}
              {selectedVehicle.color ? ` · ${selectedVehicle.color}` : ''}
            </Text>
          </View>
        ) : null}

        {error ? (
          <Text className="mt-3 text-sm text-danger">{error}</Text>
        ) : null}

        <View className="mt-6">
          <Button
            label="Continuar"
            onPress={onContinue}
            loading={createDraft.isPending}
            disabled={!vehicleId || !policyId}
          />
        </View>
      </ScrollView>
    </Screen>
  )
}
