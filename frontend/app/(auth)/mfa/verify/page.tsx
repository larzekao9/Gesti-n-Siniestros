import type { Metadata } from 'next'
import { MFAVerifyForm } from '@/components/auth/MFAVerifyForm'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

export const metadata: Metadata = {
  title: 'Verificar Código MFA',
}

export default function MFAVerifyPage() {
  return (
    <Card className="shadow-md">
      <CardHeader className="text-center space-y-1">
        <CardTitle className="text-xl">Verificar autenticación</CardTitle>
        <CardDescription>
          Ingresá el código de tu aplicación de autenticación para continuar
        </CardDescription>
      </CardHeader>
      <CardContent>
        <MFAVerifyForm />
      </CardContent>
    </Card>
  )
}
