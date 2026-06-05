import { Pressable, View, type ViewProps } from 'react-native'

interface CardProps extends ViewProps {
  onPress?: () => void
  className?: string
}

export function Card({ onPress, className = '', children, ...props }: CardProps) {
  const base = `rounded-2xl border border-line bg-white p-4 ${className}`
  if (onPress) {
    return (
      <Pressable
        onPress={onPress}
        accessibilityRole="button"
        className={`${base} active:bg-background`}
      >
        {children}
      </Pressable>
    )
  }
  return (
    <View className={base} {...props}>
      {children}
    </View>
  )
}
