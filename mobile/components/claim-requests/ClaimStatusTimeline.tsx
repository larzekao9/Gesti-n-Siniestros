import { Text, View } from 'react-native'

import { statusStyle } from '@/lib/theme'
import { formatDateTime } from '@/lib/utils/format'
import type { InsuredTimelineEntry } from '@/types/claim'

// Línea de tiempo vertical del expediente (CU-06).
export function ClaimStatusTimeline({ entries }: { entries: InsuredTimelineEntry[] }) {
  if (entries.length === 0) {
    return <Text className="text-sm text-muted">Sin movimientos todavía.</Text>
  }
  return (
    <View className="gap-0">
      {entries.map((e, i) => {
        const s = statusStyle(e.to_status)
        const isLast = i === entries.length - 1
        return (
          <View key={`${e.to_status}-${i}`} className="flex-row gap-3">
            <View className="items-center">
              <View
                className="mt-1 h-3 w-3 rounded-full"
                style={{ backgroundColor: s.dot }}
              />
              {!isLast ? <View className="w-0.5 flex-1 bg-line" /> : null}
            </View>
            <View className={`flex-1 ${isLast ? '' : 'pb-5'}`}>
              <Text className="text-sm font-semibold text-brand">{s.label}</Text>
              <Text className="text-xs text-muted">{formatDateTime(e.created_at)}</Text>
            </View>
          </View>
        )
      })}
    </View>
  )
}
