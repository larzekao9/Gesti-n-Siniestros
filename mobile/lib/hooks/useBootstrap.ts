// Restaura la sesión al abrir la app: si hay refresh token guardado, el primer
// getMe() dispara el refresh vía interceptor y rellena la cuenta. Si falla, queda
// deslogueado. Devuelve `ready` cuando terminó de intentar.
import { useEffect, useState } from 'react'

import { getMe } from '../api/insured-auth'
import { useAuthStore } from '../stores/authStore'

export function useBootstrap(): { ready: boolean } {
  const [ready, setReady] = useState(false)
  const hydrate = useAuthStore((s) => s.hydrate)

  useEffect(() => {
    let cancelled = false
    async function run() {
      await hydrate()
      const refresh = await useAuthStore.getState().getRefreshToken()
      if (refresh) {
        try {
          const account = await getMe()
          if (!cancelled) {
            useAuthStore.setState({ account })
          }
        } catch {
          if (!cancelled) await useAuthStore.getState().logout()
        }
      }
      if (!cancelled) setReady(true)
    }
    run()
    return () => {
      cancelled = true
    }
  }, [hydrate])

  return { ready }
}
