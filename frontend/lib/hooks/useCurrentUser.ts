'use client'

import { useEffect, useState } from 'react'
import { useAuthStore } from '@/lib/stores/authStore'
import { authApi } from '@/lib/api/auth'

export function useCurrentUser() {
  const { user, setAuth, accessToken, tenantSlug, clearAuth } = useAuthStore()
  const [isLoading, setIsLoading] = useState(!user)

  useEffect(() => {
    if (user) {
      setIsLoading(false)
      return
    }

    let cancelled = false

    async function fetch() {
      try {
        const me = await authApi.getMe()
        if (!cancelled) {
          setAuth(
            me,
            accessToken ?? '',
            localStorage.getItem('siniestros_rt') ?? '',
            tenantSlug ?? ''
          )
        }
      } catch {
        if (!cancelled) {
          clearAuth()
        }
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }

    if (accessToken) {
      fetch()
    } else {
      setIsLoading(false)
    }

    return () => {
      cancelled = true
    }
  }, [user, accessToken, tenantSlug, setAuth, clearAuth])

  return { user, isLoading }
}
