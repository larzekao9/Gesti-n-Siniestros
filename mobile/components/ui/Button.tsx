import { ActivityIndicator, Pressable, Text, View } from 'react-native'
import type { LucideIcon } from 'lucide-react-native'

import { colors } from '@/lib/theme'

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger'

interface ButtonProps {
  label: string
  onPress?: () => void
  variant?: Variant
  loading?: boolean
  disabled?: boolean
  icon?: LucideIcon
  fullWidth?: boolean
}

const VARIANTS: Record<Variant, { container: string; text: string; spinner: string }> = {
  primary: { container: 'bg-accent active:bg-accent-600', text: 'text-white', spinner: colors.white },
  secondary: {
    container: 'bg-white border border-line active:bg-background',
    text: 'text-brand',
    spinner: colors.brand,
  },
  ghost: { container: 'bg-transparent active:bg-background', text: 'text-brand', spinner: colors.brand },
  danger: { container: 'bg-danger active:opacity-90', text: 'text-white', spinner: colors.white },
}

export function Button({
  label,
  onPress,
  variant = 'primary',
  loading = false,
  disabled = false,
  icon: Icon,
  fullWidth = true,
}: ButtonProps) {
  const v = VARIANTS[variant]
  const isDisabled = disabled || loading
  return (
    <Pressable
      onPress={onPress}
      disabled={isDisabled}
      accessibilityRole="button"
      accessibilityState={{ disabled: isDisabled, busy: loading }}
      className={`h-14 flex-row items-center justify-center gap-2 rounded-2xl px-5 ${v.container} ${
        fullWidth ? 'w-full' : ''
      } ${isDisabled ? 'opacity-50' : ''}`}
    >
      {loading ? (
        <ActivityIndicator color={v.spinner} />
      ) : (
        <View className="flex-row items-center gap-2">
          {Icon ? <Icon size={20} color={variant === 'secondary' || variant === 'ghost' ? colors.brand : colors.white} /> : null}
          <Text className={`font-semibold text-base ${v.text}`}>{label}</Text>
        </View>
      )}
    </Pressable>
  )
}
