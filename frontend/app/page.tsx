import { redirect } from 'next/navigation'

/**
 * Root route — the middleware handles the final redirect destination
 * (login or dashboard based on auth state). This is a safety fallback.
 */
export default function RootPage() {
  redirect('/login')
}
