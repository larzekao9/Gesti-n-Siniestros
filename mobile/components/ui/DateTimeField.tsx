import { useState } from 'react'
import { Platform, Pressable, Text, View } from 'react-native'
import DateTimePicker, {
  type DateTimePickerEvent,
} from '@react-native-community/datetimepicker'
import { Calendar, Clock } from 'lucide-react-native'

import { colors } from '@/lib/theme'

interface DateTimeFieldProps {
  label?: string
  mode: 'date' | 'time'
  value: string // 'YYYY-MM-DD' (date) o 'HH:MM' (time); '' = sin valor
  onChange: (value: string) => void
  error?: string
  required?: boolean
  placeholder?: string
}

function pad(n: number): string {
  return String(n).padStart(2, '0')
}

function parseToDate(mode: 'date' | 'time', value: string): Date {
  const now = new Date()
  if (!value) return now
  if (mode === 'date') {
    const [y, m, d] = value.split('-').map(Number)
    if (y && m && d) return new Date(y, m - 1, d)
    return now
  }
  const [h, min] = value.split(':').map(Number)
  const dt = new Date()
  if (!Number.isNaN(h)) dt.setHours(h, Number.isNaN(min) ? 0 : min, 0, 0)
  return dt
}

function format(mode: 'date' | 'time', d: Date): string {
  if (mode === 'date') return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`
}

// Campo de fecha/hora con el selector NATIVO del sistema (rueda/calendario),
// en vez de tipear a mano. Android abre un diálogo y se cierra al elegir; iOS
// muestra el selector compacto.
export function DateTimeField({
  label,
  mode,
  value,
  onChange,
  error,
  required,
  placeholder,
}: DateTimeFieldProps) {
  const [show, setShow] = useState(false)
  const Icon = mode === 'date' ? Calendar : Clock
  const fallback = mode === 'date' ? 'Elegí una fecha' : 'Elegí una hora'

  function handleChange(event: DateTimePickerEvent, selected?: Date) {
    // Android: el diálogo se cierra solo; lo reflejamos en el estado.
    setShow(Platform.OS === 'ios')
    if (event.type === 'dismissed') {
      setShow(false)
      return
    }
    if (selected) onChange(format(mode, selected))
  }

  return (
    <View className="gap-1.5">
      {label ? (
        <Text className="text-sm font-medium text-brand">
          {label}
          {required ? <Text className="text-danger"> *</Text> : null}
        </Text>
      ) : null}

      <Pressable
        onPress={() => setShow(true)}
        accessibilityRole="button"
        accessibilityLabel={value || placeholder || fallback}
        className={`min-h-[52px] flex-row items-center justify-between rounded-xl border bg-white px-4 py-3 ${
          error ? 'border-danger' : 'border-line'
        }`}
      >
        <Text className={value ? 'text-base text-brand' : 'text-base text-muted-fg'}>
          {value || placeholder || fallback}
        </Text>
        <Icon size={20} color={colors.muted} />
      </Pressable>

      {error ? <Text className="text-sm text-danger">{error}</Text> : null}

      {show ? (
        <DateTimePicker
          value={parseToDate(mode, value)}
          mode={mode}
          is24Hour
          display={Platform.OS === 'ios' ? 'spinner' : 'default'}
          onChange={handleChange}
        />
      ) : null}

      {Platform.OS === 'ios' && show ? (
        <Pressable
          onPress={() => setShow(false)}
          className="self-end rounded-lg bg-accent-50 px-4 py-2"
        >
          <Text className="text-sm font-semibold text-accent">Listo</Text>
        </Pressable>
      ) : null}
    </View>
  )
}
