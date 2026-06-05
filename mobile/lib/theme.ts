// Tokens de color (paleta "Trust & Authority") para usos fuera de Tailwind:
// colores de íconos, status bars, tints de Pressable, y mapeo de estados.

export const colors = {
  brand: '#0F172A',
  brand600: '#1E293B',
  accent: '#16A34A',
  accent50: '#F0FDF4',
  surface: '#FFFFFF',
  background: '#F8FAFC',
  muted: '#64748B',
  mutedFg: '#94A3B8',
  line: '#E2E8F0',
  danger: '#DC2626',
  danger50: '#FEF2F2',
  warning: '#D97706',
  warning50: '#FFFBEB',
  info: '#2563EB',
  info50: '#EFF6FF',
  white: '#FFFFFF',
}

type StatusStyle = { label: string; bg: string; fg: string; dot: string }

// Estados de solicitud (claim_request) y expediente (claim) unificados para la
// vista "Mis reclamos" del asegurado. Color NO es el único indicador: siempre va
// con label de texto (regla a11y color-not-only).
export const STATUS_STYLES: Record<string, StatusStyle> = {
  // claim_request
  draft: { label: 'Borrador', bg: '#F1F5F9', fg: '#475569', dot: '#94A3B8' },
  submitted: { label: 'Enviada', bg: colors.info50, fg: '#1D4ED8', dot: colors.info },
  under_intake_review: { label: 'En revisión', bg: colors.warning50, fg: '#B45309', dot: colors.warning },
  formalized: { label: 'Expediente abierto', bg: colors.accent50, fg: '#15803D', dot: colors.accent },
  rejected_at_intake: { label: 'Rechazada', bg: colors.danger50, fg: '#B91C1C', dot: colors.danger },
  // claim
  registered: { label: 'Registrado', bg: colors.info50, fg: '#1D4ED8', dot: colors.info },
  in_review: { label: 'En análisis', bg: colors.warning50, fg: '#B45309', dot: colors.warning },
  observed: { label: 'Observado', bg: colors.warning50, fg: '#B45309', dot: colors.warning },
  docs_pending: { label: 'Documentos pendientes', bg: colors.warning50, fg: '#B45309', dot: colors.warning },
  in_evaluation: { label: 'En evaluación', bg: colors.info50, fg: '#1D4ED8', dot: colors.info },
  approved: { label: 'Aprobado', bg: colors.accent50, fg: '#15803D', dot: colors.accent },
  rejected: { label: 'Rechazado', bg: colors.danger50, fg: '#B91C1C', dot: colors.danger },
  closed: { label: 'Cerrado', bg: '#F1F5F9', fg: '#475569', dot: '#94A3B8' },
}

export function statusStyle(status: string): StatusStyle {
  return (
    STATUS_STYLES[status] ?? {
      label: status,
      bg: '#F1F5F9',
      fg: '#475569',
      dot: '#94A3B8',
    }
  )
}
