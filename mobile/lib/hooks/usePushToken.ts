// Registra el Expo push token tras el login (CU-01 paso 5). Best-effort.
//
// Importante: en Expo Go (SDK 53+) el push remoto fue removido y, peor aún,
// el solo hecho de IMPORTAR `expo-notifications` dispara un side-effect que
// lanza un error. Por eso NO lo importamos a nivel de módulo: cargamos
// `expo-notifications`/`expo-device` de forma dinámica y únicamente cuando NO
// estamos en Expo Go (es decir, en un development build / APK de EAS).
import { useEffect } from 'react'
import { Platform } from 'react-native'
import Constants, { ExecutionEnvironment } from 'expo-constants'

import { registerDeviceToken } from '../api/insured-auth'
import { useAuthStore } from '../stores/authStore'

export function usePushToken() {
  const account = useAuthStore((s) => s.account)

  useEffect(() => {
    if (!account) return
    // En Expo Go: salir ANTES de tocar expo-notifications (evita el error).
    if (Constants.executionEnvironment === ExecutionEnvironment.StoreClient) return

    let cancelled = false

    async function register() {
      try {
        const Device = await import('expo-device')
        if (!Device.isDevice) return // los emuladores no soportan push

        const Notifications = await import('expo-notifications')

        Notifications.setNotificationHandler({
          handleNotification: async () => ({
            shouldShowBanner: true,
            shouldShowList: true,
            shouldPlaySound: true,
            shouldSetBadge: true,
          }),
        })

        const settings = await Notifications.getPermissionsAsync()
        let status = settings.status
        if (status !== 'granted') {
          status = (await Notifications.requestPermissionsAsync()).status
        }
        if (status !== 'granted') return

        if (Platform.OS === 'android') {
          await Notifications.setNotificationChannelAsync('default', {
            name: 'default',
            importance: Notifications.AndroidImportance.DEFAULT,
          })
        }

        const projectId =
          Constants.expoConfig?.extra?.eas?.projectId ??
          Constants.easConfig?.projectId
        const tokenResp = await Notifications.getExpoPushTokenAsync(
          projectId ? { projectId } : undefined
        )
        if (cancelled || !tokenResp.data) return

        await registerDeviceToken({
          expo_push_token: tokenResp.data,
          platform: Platform.OS === 'ios' ? 'ios' : 'android',
        })
      } catch {
        // Silencioso: el push es opcional. La app funciona sin él.
      }
    }

    register()
    return () => {
      cancelled = true
    }
  }, [account])
}
