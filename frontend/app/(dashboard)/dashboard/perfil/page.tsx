'use client'

import { useState } from 'react'
import { Shield, Mail, User } from 'lucide-react'
import { useAuthStore } from '@/lib/stores/authStore'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ChangePasswordDialog } from '@/components/profile/ChangePasswordDialog'

const ROLE_LABELS: Record<string, string> = {
  admin: 'Administrador',
  supervisor: 'Supervisor',
  analyst: 'Analista',
}

const ROLE_STYLES: Record<string, string> = {
  admin: 'bg-purple-100 text-purple-800',
  supervisor: 'bg-blue-100 text-blue-800',
  analyst: 'bg-emerald-100 text-emerald-800',
}

export default function ProfilePage() {
  const { user } = useAuthStore()
  const [showPasswordDialog, setShowPasswordDialog] = useState(false)

  if (!user) {
    return (
      <div className="p-6 text-slate-500">Cargando perfil...</div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Mi perfil</h1>
        <p className="text-sm text-slate-500 mt-1">
          Información de tu cuenta y opciones de seguridad
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Información personal</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100">
              <User className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-slate-500">Nombre</p>
              <p className="font-medium text-slate-900">{user.full_name}</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100">
              <Mail className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-slate-500">Correo electrónico</p>
              <p className="font-medium text-slate-900">{user.email}</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100">
              <Shield className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-slate-500">Rol</p>
              <span
                className={`inline-block mt-0.5 px-2 py-0.5 rounded-full text-xs font-medium ${ROLE_STYLES[user.role] ?? 'bg-slate-100 text-slate-800'}`}
              >
                {ROLE_LABELS[user.role] ?? user.role}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Seguridad</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-slate-900">Cambiar contraseña</p>
              <p className="text-sm text-slate-500">
                Actualizá tu contraseña periódicamente para mantener tu cuenta
                segura
              </p>
            </div>
            <Button
              variant="outline"
              onClick={() => setShowPasswordDialog(true)}
            >
              Cambiar contraseña
            </Button>
          </div>
        </CardContent>
      </Card>

      <ChangePasswordDialog
        open={showPasswordDialog}
        onClose={() => setShowPasswordDialog(false)}
      />
    </div>
  )
}
