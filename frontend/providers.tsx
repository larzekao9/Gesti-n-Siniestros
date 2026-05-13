'use client'

import { useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60_000,
            refetchOnWindowFocus: false,
            retry: (failureCount, error) => {
              // Do not retry on 401/403/404
              if (
                error != null &&
                typeof error === 'object' &&
                'response' in error
              ) {
                const status = (error as { response?: { status?: number } })
                  .response?.status
                if (status === 401 || status === 403 || status === 404) {
                  return false
                }
              }
              return failureCount < 2
            },
          },
          mutations: {
            retry: false,
          },
        },
      })
  )

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <Toaster richColors position="top-right" closeButton />
    </QueryClientProvider>
  )
}
