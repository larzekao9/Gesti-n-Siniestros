import { Text, View } from 'react-native'

import { statusStyle } from '@/lib/theme'

// Badge de estado. Color + dot + texto (nunca solo color — regla a11y).
export function StatusBadge({ status }: { status: string }) {
  const s = statusStyle(status)
  return (
    <View
      className="flex-row items-center gap-1.5 self-start rounded-full px-2.5 py-1"
      style={{ backgroundColor: s.bg }}
      accessibilityRole="text"
      accessibilityLabel={`Estado: ${s.label}`}
    >
      <View
        className="h-2 w-2 rounded-full"
        style={{ backgroundColor: s.dot }}
      />
      <Text className="text-xs font-semibold" style={{ color: s.fg }}>
        {s.label}
      </Text>
    </View>
  )
}
