import { useState } from 'react'
import { Modal, Pressable, ScrollView, Text, View } from 'react-native'
import { useSafeAreaInsets } from 'react-native-safe-area-context'
import { Check, ChevronDown, X } from 'lucide-react-native'

import { colors } from '@/lib/theme'

export interface Option {
  value: string
  label: string
  sublabel?: string
}

interface OptionPickerProps {
  label?: string
  placeholder: string
  options: Option[]
  value: string | null
  onChange: (value: string) => void
  error?: string
  required?: boolean
  emptyHint?: string
}

// Select accesible: campo pressable que abre un bottom-sheet modal con opciones.
export function OptionPicker({
  label,
  placeholder,
  options,
  value,
  onChange,
  error,
  required,
  emptyHint,
}: OptionPickerProps) {
  const [open, setOpen] = useState(false)
  const insets = useSafeAreaInsets()
  const selected = options.find((o) => o.value === value)

  return (
    <View className="gap-1.5">
      {label ? (
        <Text className="text-sm font-medium text-brand">
          {label}
          {required ? <Text className="text-danger"> *</Text> : null}
        </Text>
      ) : null}

      <Pressable
        onPress={() => setOpen(true)}
        accessibilityRole="button"
        accessibilityLabel={selected ? selected.label : placeholder}
        className={`min-h-[52px] flex-row items-center justify-between rounded-xl border bg-white px-4 py-3 ${
          error ? 'border-danger' : 'border-line'
        }`}
      >
        <View className="flex-1 pr-2">
          {selected ? (
            <>
              <Text className="text-base text-brand">{selected.label}</Text>
              {selected.sublabel ? (
                <Text className="text-xs text-muted">{selected.sublabel}</Text>
              ) : null}
            </>
          ) : (
            <Text className="text-base text-muted-fg">{placeholder}</Text>
          )}
        </View>
        <ChevronDown size={20} color={colors.muted} />
      </Pressable>

      {error ? <Text className="text-sm text-danger">{error}</Text> : null}

      <Modal
        visible={open}
        transparent
        animationType="slide"
        statusBarTranslucent
        navigationBarTranslucent
        onRequestClose={() => setOpen(false)}
      >
        {/* Scrim a pantalla completa (cubre tab bar + barra del sistema). */}
        <Pressable
          className="flex-1 justify-end bg-black/50"
          onPress={() => setOpen(false)}
        >
          {/* La hoja blanca llega hasta el borde inferior real (safe-area). */}
          <Pressable
            className="max-h-[75%] rounded-t-3xl bg-white pt-3"
            style={{ paddingBottom: insets.bottom + 16 }}
          >
            <View className="mb-2 flex-row items-center justify-between px-5 py-2">
              <Text className="text-lg font-semibold text-brand">{placeholder}</Text>
              <Pressable
                onPress={() => setOpen(false)}
                hitSlop={10}
                accessibilityLabel="Cerrar"
              >
                <X size={22} color={colors.muted} />
              </Pressable>
            </View>
            {options.length === 0 ? (
              <Text className="px-5 py-6 text-center text-sm text-muted">
                {emptyHint ?? 'No hay opciones disponibles'}
              </Text>
            ) : (
              <ScrollView>
                {options.map((opt) => {
                  const isSel = opt.value === value
                  return (
                    <Pressable
                      key={opt.value}
                      onPress={() => {
                        onChange(opt.value)
                        setOpen(false)
                      }}
                      className="flex-row items-center justify-between border-b border-line px-5 py-4 active:bg-background"
                    >
                      <View className="flex-1 pr-3">
                        <Text className="text-base text-brand">{opt.label}</Text>
                        {opt.sublabel ? (
                          <Text className="text-xs text-muted">{opt.sublabel}</Text>
                        ) : null}
                      </View>
                      {isSel ? <Check size={20} color={colors.accent} /> : null}
                    </Pressable>
                  )
                })}
              </ScrollView>
            )}
          </Pressable>
        </Pressable>
      </Modal>
    </View>
  )
}
