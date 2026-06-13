import { useState } from 'react'
import { ActivityIndicator, Image, Pressable, Text, View } from 'react-native'
import { Sparkles } from 'lucide-react-native'

import { analyzeEvidenceDamage } from '@/lib/api/ai'
import { apiErrorMessage } from '@/lib/api/client'
import { colors } from '@/lib/theme'
import type { Evidence } from '@/types/evidence'
import type { DamageAssessment } from '@/types/ai-analysis'

interface Props {
  requestId: string
  evidence: Evidence
}

const SEVERITY_STYLE: Record<string, { chip: string; label: string }> = {
  leve: { chip: 'bg-green-100', label: 'Leve' },
  moderado: { chip: 'bg-amber-100', label: 'Moderado' },
  severo: { chip: 'bg-red-100', label: 'Severo' },
  indeterminado: { chip: 'bg-slate-100', label: 'Indeterminado' },
}

// CU-33: el asegurado pide el análisis de daño de una foto. El resultado es
// apoyo informativo (no bloquea el envío de la solicitud).
export function DamageAnalysisCard({ requestId, evidence }: Props) {
  const [result, setResult] = useState<DamageAssessment | null>(null)
  const [explanation, setExplanation] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function analyze() {
    setLoading(true)
    setError(null)
    try {
      const analysis = await analyzeEvidenceDamage(requestId, evidence.id)
      if (analysis.status === 'error') {
        setError('No se pudo analizar la imagen. Intentá de nuevo.')
      } else {
        setResult((analysis.payload as unknown as DamageAssessment) ?? null)
        setExplanation(analysis.explanation)
      }
    } catch (err) {
      setError(apiErrorMessage(err, 'No se pudo analizar la imagen'))
    } finally {
      setLoading(false)
    }
  }

  const severity = result ? SEVERITY_STYLE[result.severity] ?? SEVERITY_STYLE.indeterminado : null

  return (
    <View className="flex-row gap-3 rounded-2xl border border-line bg-white p-3">
      <Image
        source={{ uri: evidence.download_url ?? '' }}
        className="h-16 w-16 rounded-xl"
        resizeMode="cover"
      />
      <View className="flex-1 justify-center">
        {result ? (
          <>
            <View className="flex-row items-center gap-2">
              <Text className="font-semibold text-brand" numberOfLines={1}>
                {result.damage_type}
              </Text>
              {severity ? (
                <View className={`rounded-full px-2 py-0.5 ${severity.chip}`}>
                  <Text className="text-[11px] font-medium text-slate-700">{severity.label}</Text>
                </View>
              ) : null}
            </View>
            {explanation ? (
              <Text className="mt-1 text-xs leading-4 text-muted" numberOfLines={3}>
                {explanation}
              </Text>
            ) : null}
            <Text className="mt-1 text-[11px] text-muted">
              Confianza {Math.round((result.confidence ?? 0) * 100)}%
            </Text>
          </>
        ) : error ? (
          <>
            <Text className="text-xs text-red-600">{error}</Text>
            <Pressable onPress={analyze} hitSlop={8} className="mt-1">
              <Text className="text-xs font-semibold text-brand">Reintentar</Text>
            </Pressable>
          </>
        ) : (
          <Pressable
            onPress={analyze}
            disabled={loading}
            className="flex-row items-center gap-2 self-start rounded-xl bg-brand/10 px-3 py-2"
            accessibilityLabel="Analizar daño con inteligencia artificial"
          >
            {loading ? (
              <ActivityIndicator size="small" color={colors.brand} />
            ) : (
              <Sparkles size={16} color={colors.brand} />
            )}
            <Text className="text-sm font-semibold text-brand">
              {loading ? 'Analizando…' : 'Analizar daño (IA)'}
            </Text>
          </Pressable>
        )}
      </View>
    </View>
  )
}
