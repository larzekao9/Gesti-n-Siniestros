import { ActivityIndicator, Text, View } from 'react-native'

import { colors } from '@/lib/theme'

export function Loading({ label }: { label?: string }) {
  return (
    <View className="flex-1 items-center justify-center gap-3 bg-background">
      <ActivityIndicator size="large" color={colors.accent} />
      {label ? <Text className="text-sm text-muted">{label}</Text> : null}
    </View>
  )
}
