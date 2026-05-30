'use client'

import { useEffect, useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import Link from 'next/link'
import { Loader2, LayoutDashboard, FileText, Users, UserPlus, Clipboard, Car, User, BarChart3, LogOut, Shield } from 'lucide-react'
import { toast } from 'sonner'
import { isAxiosError } from 'axios'

import { useAuthStore, getRefreshToken } from '@/lib/stores/authStore'
import { authApi } from '@/lib/api/auth'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

const NAV_ITEMS = [
  {
    href: '/dashboard',
    label: 'Dashboard',
    icon: LayoutDashboard,
  },
  {
    href: '/dashboard/asegurados',
    label: 'Asegurados',
    icon: UserPlus,
  },
  {
    href: '/dashboard/polizas',
    label: 'Pólizas',
    icon: Clipboard,
  },
  {
    href: '/dashboard/vehiculos',
    label: 'Vehículos',
    icon: Car,
  },
  {
    href: '/dashboard/usuarios',
    label: 'Usuarios',
    icon: Users,
    roles: ['admin'] as const,
  },
  {
    href: '/dashboard/reportes',
    label: 'Reportes',
    icon: BarChart3,
  },
  {
    href: '/dashboard/expedientes',
    label: 'Expedientes',
    icon: FileText,
  },
  {
    href: '/dashboard/solicitudes',
    label: 'Solicitudes',
    icon: FileText,
  },
  {
    href: '/dashboard/perfil',
    label: 'Perfil',
    icon: User,
  },
] satisfies Array<{
  href: string
  label: string
  icon: React.ComponentType<{ className?: string }>
  roles?: Array<'admin' | 'supervisor' | 'analyst'>
}>

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const pathname = usePathname()
  const { user, clearAuth, isLoading, setLoading } = useAuthStore()
  const [hasHydrated, setHasHydrated] = useState(false)

  // DT-15: esperar a que Zustand persist termine de hidratar antes de decidir
  // si redirigir. Sin esto, al recargar la pagina `user` es null por un tick
  // y el redirect se dispara antes de que se restaure desde localStorage.
  // (DT-17: hot reload por polling de Webpack en docker-compose.override.yml)
  useEffect(() => {
    setHasHydrated(useAuthStore.persist.hasHydrated())
    const unsub = useAuthStore.persist.onFinishHydration(() => setHasHydrated(true))
    return unsub
  }, [])

  useEffect(() => {
    if (hasHydrated && !user) {
      router.replace('/login')
    }
  }, [hasHydrated, user, router])

  const handleLogout = async () => {
    setLoading(true)
    try {
      const refreshToken = getRefreshToken()
      if (refreshToken) {
        await authApi.logout(refreshToken)
      }
    } catch (error: unknown) {
      if (isAxiosError(error)) {
        console.error('[DashboardLayout] logout error:', error)
      }
      // Proceed with local logout regardless of API error
    } finally {
      clearAuth()
      toast.success('Sesión cerrada correctamente')
      router.push('/login')
      setLoading(false)
    }
  }

  if (!hasHydrated || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" aria-label={hasHydrated ? 'Redirigiendo...' : 'Restaurando sesion...'} />
      </div>
    )
  }

  const visibleNavItems = NAV_ITEMS.filter(
    (item) => !item.roles || item.roles.includes(user.role as 'admin')
  )

  return (
    <div className="flex min-h-screen bg-slate-50">
      {/* Sidebar */}
      <aside
        className="hidden md:flex w-64 flex-col bg-white border-r border-slate-200 fixed inset-y-0 left-0 z-20"
        aria-label="Navegación principal"
      >
        {/* Brand */}
        <div className="flex items-center gap-3 px-6 py-5 border-b border-slate-200">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-blue-600 flex-shrink-0">
            <Shield className="h-4 w-4 text-white" aria-hidden="true" />
          </div>
          <span className="font-semibold text-slate-900 text-sm leading-tight">
            Gestión Siniestros
          </span>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-1" aria-label="Secciones de la plataforma">
          {visibleNavItems.map((item) => {
            const isActive =
              item.href === '/dashboard'
                ? pathname === '/dashboard'
                : pathname.startsWith(item.href)
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                )}
                aria-current={isActive ? 'page' : undefined}
              >
                <item.icon className="h-4 w-4 flex-shrink-0" aria-hidden="true" />
                {item.label}
              </Link>
            )
          })}
        </nav>

        {/* User section */}
        <div className="px-3 py-4 border-t border-slate-200 space-y-3">
          <div className="px-3">
            <p className="text-sm font-medium text-slate-900 truncate">{user.full_name}</p>
            <p className="text-xs text-slate-500 truncate">{user.email}</p>
            <span className="inline-block mt-1 rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700 capitalize">
              {user.role === 'admin'
                ? 'Administrador'
                : user.role === 'supervisor'
                ? 'Supervisor'
                : 'Analista'}
            </span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleLogout}
            disabled={isLoading}
            className="w-full justify-start text-slate-600 hover:text-red-600 hover:bg-red-50"
            aria-label="Cerrar sesión"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            ) : (
              <LogOut className="h-4 w-4" aria-hidden="true" />
            )}
            Cerrar sesión
          </Button>
        </div>
      </aside>

      {/* Mobile header */}
      <header className="md:hidden fixed top-0 inset-x-0 z-20 flex items-center justify-between bg-white border-b border-slate-200 px-4 h-14">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-blue-600">
            <Shield className="h-4 w-4 text-white" aria-hidden="true" />
          </div>
          <span className="font-semibold text-slate-900 text-sm">Gestión Siniestros</span>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={handleLogout}
          disabled={isLoading}
          aria-label="Cerrar sesión"
        >
          <LogOut className="h-4 w-4" aria-hidden="true" />
        </Button>
      </header>

      {/* Mobile bottom nav */}
      <nav
        className="md:hidden fixed bottom-0 inset-x-0 z-20 flex bg-white border-t border-slate-200"
        aria-label="Navegación móvil"
      >
        {visibleNavItems.map((item) => {
          const isActive =
            item.href === '/dashboard'
              ? pathname === '/dashboard'
              : pathname.startsWith(item.href)
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex flex-1 flex-col items-center justify-center gap-1 py-2 text-xs font-medium transition-colors',
                isActive
                  ? 'text-blue-600'
                  : 'text-slate-500 hover:text-slate-900'
              )}
              aria-current={isActive ? 'page' : undefined}
            >
              <item.icon className="h-5 w-5" aria-hidden="true" />
              <span>{item.label}</span>
            </Link>
          )
        })}
      </nav>

      {/* Main content */}
      <main className="flex-1 md:ml-64 pt-14 md:pt-0 pb-16 md:pb-0">
        <div className="max-w-7xl mx-auto p-4 md:p-8">{children}</div>
      </main>
    </div>
  )
}
