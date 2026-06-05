import { ReactNode } from 'react'
import { View } from 'react-native'
import { SafeAreaView, type Edge } from 'react-native-safe-area-context'

interface ScreenProps {
  children: ReactNode
  className?: string
  edges?: Edge[]
}

// Wrapper con safe-area + fondo de la app. Usar en cada pantalla.
export function Screen({
  children,
  className = '',
  edges = ['top', 'bottom'],
}: ScreenProps) {
  return (
    <SafeAreaView edges={edges} className="flex-1 bg-background">
      <View className={`flex-1 ${className}`}>{children}</View>
    </SafeAreaView>
  )
}
