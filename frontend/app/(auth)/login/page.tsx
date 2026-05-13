import type { Metadata } from 'next'
import { LoginForm } from '@/components/auth/LoginForm'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

export const metadata: Metadata = {
  title: 'Iniciar Sesión',
}

export default function LoginPage() {
  return (
    <Card className="shadow-md">
      <CardHeader className="text-center space-y-2">
        {/* Logo / brand mark */}
        <div
          className="mx-auto flex h-10 w-10 items-center justify-center rounded-lg bg-blue-600"
          aria-hidden="true"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="h-5 w-5 text-white"
            aria-hidden="true"
          >
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
          </svg>
        </div>
        <CardTitle className="text-xl">Gestión Siniestros</CardTitle>
        <CardDescription>
          Ingresá tus credenciales para acceder a la plataforma
        </CardDescription>
      </CardHeader>
      <CardContent>
        <LoginForm />
      </CardContent>
    </Card>
  )
}
