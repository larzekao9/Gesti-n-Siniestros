// Deep-link al tocar una notificación push del SO: lee `data` (entity_type /
// entity_id, que el backend ya envía en cada push) y navega a la pantalla
// correspondiente. Cubre el caso "app en background/cerrada" (cold start) y el
// caso "app abierta".
//
// Mismo cuidado que usePushToken: en Expo Go importar `expo-notifications`
// dispara un error, así que se carga dinámicamente y solo fuera de Expo Go.
import { useEffect } from 'react'
import { useRouter } from 'expo-router'
import Constants, { ExecutionEnvironment } from 'expo-constants'

type PushData = {
  entity_type?: string
  entity_id?: string | null
}

export function usePushNavigation() {
  const router = useRouter()

  useEffect(() => {
    if (Constants.executionEnvironment === ExecutionEnvironment.StoreClient) return

    let sub: { remove: () => void } | undefined
    let cancelled = false

    function navigate(data: PushData | undefined) {
      if (!data) return
      const { entity_type, entity_id } = data
      if (entity_type === 'claim' && entity_id) {
        router.push(`/reclamo/${entity_id}`)
      } else if (entity_type === 'claim_request' && entity_id) {
        router.push(`/solicitud/${entity_id}`)
      } else {
        // document_request u otros: no tenemos a dónde enlazar directo → avisos.
        router.push('/(tabs)/notificaciones')
      }
    }

    async function setup() {
      try {
        const Notifications = await import('expo-notifications')

        // Cold start: la app se abrió tocando un push estando cerrada.
        const last = await Notifications.getLastNotificationResponseAsync()
        if (!cancelled && last) {
          navigate(last.notification.request.content.data as PushData)
        }

        // App ya abierta: tap mientras corre.
        sub = Notifications.addNotificationResponseReceivedListener((response) => {
          navigate(response.notification.request.content.data as PushData)
        })
      } catch {
        // Silencioso: el deep-link es un extra; la app funciona sin él.
      }
    }

    setup()
    return () => {
      cancelled = true
      sub?.remove()
    }
  }, [router])
}
