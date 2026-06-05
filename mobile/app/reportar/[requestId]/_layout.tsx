import { Stack } from 'expo-router'

import { colors } from '@/lib/theme'

export default function ReportWizardLayout() {
  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: colors.brand },
        headerTintColor: colors.white,
        headerTitleStyle: { fontWeight: '700' },
        contentStyle: { backgroundColor: colors.background },
      }}
    >
      <Stack.Screen name="accidente" options={{ title: 'Datos del accidente' }} />
      <Stack.Screen name="evidencias" options={{ title: 'Evidencias' }} />
      <Stack.Screen name="confirmar" options={{ title: 'Confirmar y enviar' }} />
    </Stack>
  )
}
