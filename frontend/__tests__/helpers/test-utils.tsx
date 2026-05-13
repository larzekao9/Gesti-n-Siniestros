/**
 * Shared test utilities: custom render with QueryClient + router mocks.
 */
import React, { type ReactElement } from 'react'
import { render, type RenderOptions } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// ------------------------------------------------------------------
// QueryClient with aggressive no-retry for deterministic tests
// ------------------------------------------------------------------
function makeTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, staleTime: 0 },
      mutations: { retry: false },
    },
  })
}

// ------------------------------------------------------------------
// Wrapper
// ------------------------------------------------------------------
function AllProviders({ children }: { children: React.ReactNode }) {
  const queryClient = makeTestQueryClient()
  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

function customRender(ui: ReactElement, options?: Omit<RenderOptions, 'wrapper'>) {
  return render(ui, { wrapper: AllProviders, ...options })
}

export * from '@testing-library/react'
export { customRender as render }
