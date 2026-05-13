'use client'

import { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { Loader2, ShieldCheck, Copy, CheckCheck } from 'lucide-react'
import { toast } from 'sonner'
import { isAxiosError } from 'axios'

import { authApi } from '@/lib/api/auth'
import type { MFASetupResponse } from '@/types/auth'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

export function MFASetupCard() {
  const router = useRouter()
  const [setupData, setSetupData] = useState<MFASetupResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  const loadSetup = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await authApi.setupMFA()
      setSetupData(data)
    } catch (err: unknown) {
      const message = isAxiosError(err)
        ? ((err.response?.data as { detail?: string })?.detail ??
          'Error al configurar MFA')
        : 'Error inesperado al configurar MFA'
      setError(message)
      toast.error(message)
      console.error('[MFASetupCard] error:', err)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadSetup()
  }, [loadSetup])

  const handleCopySecret = async () => {
    if (!setupData?.secret) return
    try {
      await navigator.clipboard.writeText(setupData.secret)
      setCopied(true)
      toast.success('Clave copiada al portapapeles')
      setTimeout(() => setCopied(false), 2000)
    } catch {
      toast.error('No se pudo copiar. Copiá la clave manualmente.')
    }
  }

  if (isLoading) {
    return (
      <Card className="w-full max-w-md mx-auto">
        <CardContent className="flex flex-col items-center justify-center py-16 gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" aria-hidden="true" />
          <p className="text-sm text-slate-500">Generando configuración MFA...</p>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="w-full max-w-md mx-auto border-red-200">
        <CardHeader>
          <CardTitle className="text-red-600">Error de configuración</CardTitle>
          <CardDescription>{error}</CardDescription>
        </CardHeader>
        <CardFooter>
          <Button
            onClick={loadSetup}
            variant="outline"
            className="w-full"
            aria-label="Reintentar configuración MFA"
          >
            Reintentar
          </Button>
        </CardFooter>
      </Card>
    )
  }

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader className="text-center">
        <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-full bg-blue-100">
          <ShieldCheck className="h-6 w-6 text-blue-600" aria-hidden="true" />
        </div>
        <CardTitle>Configurar autenticación en dos pasos</CardTitle>
        <CardDescription>
          Escaneá el código QR con Google Authenticator o Authy para activar
          el segundo factor de autenticación.
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* QR Code */}
        {setupData?.qr_uri && (
          <div className="flex flex-col items-center gap-3">
            <div
              className="rounded-lg border-2 border-slate-200 p-3 bg-white"
              role="img"
              aria-label="Código QR para configurar autenticador"
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={setupData.qr_uri}
                alt="Código QR para autenticador TOTP"
                width={180}
                height={180}
                className="block"
              />
            </div>
            <p className="text-xs text-slate-500 text-center">
              Escaneá este código con tu aplicación de autenticación
            </p>
          </div>
        )}

        {/* Manual secret */}
        {setupData?.secret && (
          <div className="space-y-2">
            <p className="text-sm font-medium text-slate-700">
              O ingresá esta clave manualmente:
            </p>
            <div className="flex items-center gap-2">
              <code className="flex-1 rounded bg-slate-100 px-3 py-2 font-mono text-sm text-slate-800 break-all">
                {setupData.secret}
              </code>
              <button
                type="button"
                onClick={handleCopySecret}
                className="flex-shrink-0 rounded-md p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700 transition-colors cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600"
                aria-label="Copiar clave secreta"
              >
                {copied ? (
                  <CheckCheck className="h-4 w-4 text-green-600" aria-hidden="true" />
                ) : (
                  <Copy className="h-4 w-4" aria-hidden="true" />
                )}
              </button>
            </div>
          </div>
        )}

        <ol className="space-y-1.5 text-sm text-slate-600 list-decimal list-inside">
          <li>Instalá Google Authenticator o Authy en tu celular.</li>
          <li>Escaneá el código QR o ingresá la clave manualmente.</li>
          <li>Tocá &quot;Ya lo configuré&quot; para verificar.</li>
        </ol>
      </CardContent>

      <CardFooter className="flex flex-col gap-3">
        <Button
          className="w-full"
          onClick={() => router.push('/mfa/verify')}
          aria-label="Continuar a verificación de MFA"
        >
          Ya lo configuré — Verificar
        </Button>
        <Button
          variant="ghost"
          className="w-full text-slate-500"
          onClick={() => router.push('/dashboard')}
          aria-label="Omitir configuración de MFA por ahora"
        >
          Omitir por ahora
        </Button>
      </CardFooter>
    </Card>
  )
}
