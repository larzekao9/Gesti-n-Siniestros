import { ReactNode, useEffect, useRef } from 'react'
import { ScrollView, Text, View } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { ShieldCheck } from 'lucide-react-native'

import { colors } from '@/lib/theme'
import { useKeyboardHeight } from '@/lib/hooks/useKeyboardHeight'

// Marco visual de las pantallas de auth: header navy con marca + tarjeta blanca.
// Maneja el teclado midiendo su altura y desplazando el contenido hacia arriba —
// funciona en cualquier teléfono (incluido Android edge-to-edge del SDK 54).
export function AuthShell({
  title,
  subtitle,
  children,
}: {
  title: string
  subtitle?: string
  children: ReactNode
}) {
  const scrollRef = useRef<ScrollView>(null)
  const kbHeight = useKeyboardHeight()

  // Al abrir el teclado, desplazamos el formulario al final (donde están los
  // campos + botón) para que queden visibles encima del teclado.
  useEffect(() => {
    if (kbHeight > 0) {
      const t = setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 60)
      return () => clearTimeout(t)
    }
  }, [kbHeight])

  return (
    <SafeAreaView edges={['top']} className="flex-1 bg-brand">
      <ScrollView
        ref={scrollRef}
        contentContainerStyle={{ flexGrow: 1, paddingBottom: 24 + kbHeight }}
        keyboardShouldPersistTaps="handled"
        keyboardDismissMode="interactive"
        showsVerticalScrollIndicator={false}
      >
        <View className="items-center gap-3 px-6 pb-7 pt-8">
          <View className="h-14 w-14 items-center justify-center rounded-2xl bg-accent">
            <ShieldCheck size={28} color={colors.white} />
          </View>
          <Text className="text-2xl font-bold text-white">Mi Seguro</Text>
          <Text className="text-sm text-slate-300">Gestión de siniestros</Text>
        </View>

        <View className="flex-1 rounded-t-3xl bg-background px-6 pt-7">
          <Text className="text-xl font-bold text-brand">{title}</Text>
          {subtitle ? (
            <Text className="mt-1 text-sm leading-5 text-muted">{subtitle}</Text>
          ) : null}
          <View className="mt-6 gap-4">{children}</View>
        </View>
      </ScrollView>
    </SafeAreaView>
  )
}
