import { Text, View } from 'react-native'
import type { LucideIcon } from 'lucide-react-native'

import { colors } from '@/lib/theme'

interface EmptyStateProps {
  icon: LucideIcon
  title: string
  description?: string
  children?: React.ReactNode
}

export function EmptyState({ icon: Icon, title, description, children }: EmptyStateProps) {
  return (
    <View className="flex-1 items-center justify-center gap-3 px-8 py-12">
      <View className="h-16 w-16 items-center justify-center rounded-full bg-accent-50">
        <Icon size={30} color={colors.accent} />
      </View>
      <Text className="text-center text-lg font-semibold text-brand">{title}</Text>
      {description ? (
        <Text className="text-center text-sm leading-5 text-muted">{description}</Text>
      ) : null}
      {children ? <View className="mt-2 w-full">{children}</View> : null}
    </View>
  )
}
