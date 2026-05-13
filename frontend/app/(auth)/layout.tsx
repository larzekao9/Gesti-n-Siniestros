import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: {
    template: '%s | Gestión Siniestros',
    default: 'Autenticación | Gestión Siniestros',
  },
}

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">{children}</div>
    </div>
  )
}
