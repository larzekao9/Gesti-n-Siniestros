import { Fragment } from 'react'
import { Text, View } from 'react-native'
import { Check } from 'lucide-react-native'

import { colors } from '@/lib/theme'

const STEPS = ['Vehículo', 'Accidente', 'Evidencias', 'Confirmar']
const NODE_WIDTH = 68

// Indicador de progreso del wizard (regla multi-step-progress).
// Nodos de ancho fijo + conectores flexibles → el primer y último círculo quedan
// simétricos respecto de cada borde, con la etiqueta centrada bajo cada círculo.
export function WizardStepper({ current }: { current: number }) {
  return (
    <View className="flex-row items-start py-3">
      {STEPS.map((label, i) => {
        const done = i < current
        const active = i === current
        const isLast = i === STEPS.length - 1
        return (
          <Fragment key={label}>
            <View className="items-center" style={{ width: NODE_WIDTH }}>
              <View
                className="h-8 w-8 items-center justify-center rounded-full"
                style={{ backgroundColor: done || active ? colors.accent : colors.line }}
              >
                {done ? (
                  <Check size={16} color={colors.white} />
                ) : (
                  <Text
                    className="text-xs font-bold"
                    style={{ color: active ? colors.white : colors.muted }}
                  >
                    {i + 1}
                  </Text>
                )}
              </View>
              <Text
                className="mt-1.5 text-[10px]"
                numberOfLines={1}
                style={{
                  color: active ? colors.brand : colors.muted,
                  fontWeight: active ? '600' : '400',
                }}
              >
                {label}
              </Text>
            </View>
            {!isLast ? (
              <View
                className="h-0.5 flex-1"
                style={{ marginTop: 15, backgroundColor: done ? colors.accent : colors.line }}
              />
            ) : null}
          </Fragment>
        )
      })}
    </View>
  )
}
