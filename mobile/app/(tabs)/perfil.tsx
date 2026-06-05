import { Alert, Text, View } from 'react-native'
import { LogOut, Mail, ShieldCheck, User } from 'lucide-react-native'

import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Screen } from '@/components/ui/Screen'
import { logout as apiLogout } from '@/lib/api/insured-auth'
import { useAuthStore } from '@/lib/stores/authStore'
import { colors } from '@/lib/theme'

export default function PerfilScreen() {
  const account = useAuthStore((s) => s.account)
  const getRefreshToken = useAuthStore((s) => s.getRefreshToken)
  const logout = useAuthStore((s) => s.logout)

  async function onLogout() {
    Alert.alert('Cerrar sesión', '¿Querés salir de tu cuenta?', [
      { text: 'Cancelar', style: 'cancel' },
      {
        text: 'Cerrar sesión',
        style: 'destructive',
        onPress: async () => {
          const refresh = await getRefreshToken()
          if (refresh) {
            try {
              await apiLogout(refresh)
            } catch {
              // best-effort: igual limpiamos la sesión local
            }
          }
          await logout()
        },
      },
    ])
  }

  return (
    <Screen edges={['top']}>
      <View className="px-5 pt-3">
        <Text className="text-2xl font-bold text-brand">Mi perfil</Text>
      </View>

      <View className="gap-4 p-5">
        <Card className="items-center gap-3 py-7">
          <View className="h-20 w-20 items-center justify-center rounded-full bg-brand">
            <User size={36} color={colors.white} />
          </View>
          <View className="items-center">
            <Text className="text-lg font-semibold text-brand">Asegurado</Text>
            <View className="mt-1 flex-row items-center gap-1.5">
              <Mail size={14} color={colors.muted} />
              <Text className="text-sm text-muted">{account?.email ?? '—'}</Text>
            </View>
          </View>
        </Card>

        <Card className="flex-row items-center gap-3">
          <View className="h-10 w-10 items-center justify-center rounded-xl bg-accent-50">
            <ShieldCheck size={20} color={colors.accent} />
          </View>
          <View className="flex-1">
            <Text className="font-medium text-brand">Cuenta verificada</Text>
            <Text className="text-xs text-muted">
              Tus datos están protegidos y cifrados.
            </Text>
          </View>
        </Card>

        <View className="mt-2">
          <Button label="Cerrar sesión" variant="danger" icon={LogOut} onPress={onLogout} />
        </View>
      </View>
    </Screen>
  )
}
