import type { Metadata } from 'next'
import { MFASetupCard } from '@/components/auth/MFASetupCard'

export const metadata: Metadata = {
  title: 'Configurar Autenticación en Dos Pasos',
}

export default function MFASetupPage() {
  return <MFASetupCard />
}
