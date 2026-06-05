import { useEffect, useState } from 'react'
import { ScrollView, Text, View } from 'react-native'
import { useLocalSearchParams, useRouter } from 'expo-router'
import { Controller, useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as Location from 'expo-location'
import { MapPin } from 'lucide-react-native'

import { Button } from '@/components/ui/Button'
import { DateTimeField } from '@/components/ui/DateTimeField'
import { Input } from '@/components/ui/Input'
import { Loading } from '@/components/ui/Loading'
import { Screen } from '@/components/ui/Screen'
import { WizardStepper } from '@/components/claim-requests/WizardStepper'
import { useKeyboardHeight } from '@/lib/hooks/useKeyboardHeight'
import { apiErrorMessage } from '@/lib/api/client'
import { useMyClaimRequest } from '@/lib/hooks/useClaims'
import { useUpdateDraft } from '@/lib/hooks/useDraft'
import { colors } from '@/lib/theme'
import { todayISODate } from '@/lib/utils/format'
import {
  accidentStepSchema,
  type AccidentStepValues,
} from '@/lib/validations/claim-request'

export default function AccidenteStep() {
  const { requestId } = useLocalSearchParams<{ requestId: string }>()
  const router = useRouter()
  const { data: draft, isLoading } = useMyClaimRequest(requestId)
  const updateDraft = useUpdateDraft(requestId)

  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(null)
  const [gpsLoading, setGpsLoading] = useState(false)
  const [gpsNote, setGpsNote] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const kbHeight = useKeyboardHeight()

  const { control, handleSubmit, reset, formState: { errors } } = useForm<AccidentStepValues>({
    resolver: zodResolver(accidentStepSchema),
    defaultValues: {
      accident_date: todayISODate(),
      accident_time: '',
      accident_location: '',
      accident_description: '',
      reported_damages: '',
    },
  })

  // Prefill desde el draft guardado (auto-save).
  useEffect(() => {
    if (draft) {
      reset({
        accident_date: draft.accident_date ?? todayISODate(),
        accident_time: draft.accident_time ?? '',
        accident_location: draft.accident_location ?? '',
        accident_description: draft.accident_description ?? '',
        reported_damages: draft.reported_damages ?? '',
      })
      if (draft.accident_lat != null && draft.accident_lng != null) {
        const lat = Number(draft.accident_lat)
        const lng = Number(draft.accident_lng)
        if (!Number.isNaN(lat) && !Number.isNaN(lng)) {
          setCoords({ lat, lng })
        }
      }
    }
  }, [draft, reset])

  async function captureGPS() {
    setGpsNote(null)
    setGpsLoading(true)
    try {
      const perm = await Location.requestForegroundPermissionsAsync()
      if (!perm.granted) {
        setGpsNote('Permiso de ubicación denegado. Podés escribir la dirección a mano.')
        return
      }
      const pos = await Location.getCurrentPositionAsync({})
      setCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude })
      setGpsNote('Ubicación capturada ✓')
    } catch {
      setGpsNote('No se pudo obtener la ubicación. Escribila a mano.')
    } finally {
      setGpsLoading(false)
    }
  }

  async function onSubmit(values: AccidentStepValues) {
    setError(null)
    try {
      await updateDraft.mutateAsync({
        accident_date: values.accident_date,
        accident_time: values.accident_time || null,
        accident_location: values.accident_location,
        accident_description: values.accident_description,
        reported_damages: values.reported_damages || null,
        accident_lat: coords?.lat ?? null,
        accident_lng: coords?.lng ?? null,
      })
      router.push(`/reportar/${requestId}/evidencias`)
    } catch (err) {
      setError(apiErrorMessage(err, 'No se pudieron guardar los datos'))
    }
  }

  if (isLoading) return <Loading />

  return (
    <Screen edges={['bottom']}>
      <ScrollView
        contentContainerStyle={{ padding: 20, gap: 16, paddingBottom: 48 + kbHeight }}
        keyboardShouldPersistTaps="handled"
        keyboardDismissMode="interactive"
        showsVerticalScrollIndicator={false}
      >
        <WizardStepper current={1} />

        <Controller
          control={control}
          name="accident_date"
          render={({ field: { onChange, value } }) => (
            <DateTimeField
              label="Fecha del accidente"
              mode="date"
              value={value}
              onChange={onChange}
              error={errors.accident_date?.message}
              required
            />
          )}
        />
        <Controller
          control={control}
          name="accident_time"
          render={({ field: { onChange, value } }) => (
            <DateTimeField
              label="Hora aproximada (opcional)"
              mode="time"
              value={value ?? ''}
              onChange={onChange}
              placeholder="Tocá para elegir la hora"
              error={errors.accident_time?.message}
            />
          )}
        />
        <Controller
          control={control}
          name="accident_location"
          render={({ field: { onChange, onBlur, value } }) => (
            <Input
              label="Lugar del accidente"
              placeholder="Av. / calle, número, ciudad"
              value={value}
              onBlur={onBlur}
              onChangeText={onChange}
              error={errors.accident_location?.message}
              required
            />
          )}
        />

        <View className="gap-2">
          <Button
            label={coords ? 'Ubicación capturada ✓' : 'Usar mi ubicación actual'}
            variant="secondary"
            icon={MapPin}
            loading={gpsLoading}
            onPress={captureGPS}
          />
          {gpsNote ? (
            <Text className="text-xs" style={{ color: coords ? colors.accent : colors.muted }}>
              {gpsNote}
            </Text>
          ) : null}
          {coords ? (
            <Text className="text-xs text-muted">
              {coords.lat.toFixed(5)}, {coords.lng.toFixed(5)}
            </Text>
          ) : null}
        </View>

        <Controller
          control={control}
          name="accident_description"
          render={({ field: { onChange, onBlur, value } }) => (
            <Input
              label="¿Qué pasó?"
              placeholder="Contanos cómo ocurrió el siniestro"
              value={value}
              onBlur={onBlur}
              onChangeText={onChange}
              error={errors.accident_description?.message}
              multiline
              numberOfLines={4}
              style={{ minHeight: 110, textAlignVertical: 'top' }}
              required
            />
          )}
        />
        <Controller
          control={control}
          name="reported_damages"
          render={({ field: { onChange, onBlur, value } }) => (
            <Input
              label="Daños reportados (opcional)"
              placeholder="Ej. paragolpes delantero, faro izquierdo"
              value={value}
              onBlur={onBlur}
              onChangeText={onChange}
              error={errors.reported_damages?.message}
              multiline
              numberOfLines={3}
              style={{ minHeight: 80, textAlignVertical: 'top' }}
            />
          )}
        />

        {error ? <Text className="text-sm text-danger">{error}</Text> : null}

        <Button
          label="Continuar a evidencias"
          onPress={handleSubmit(onSubmit)}
          loading={updateDraft.isPending}
        />
      </ScrollView>
    </Screen>
  )
}
