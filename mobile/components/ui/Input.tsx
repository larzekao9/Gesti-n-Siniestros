import { forwardRef, useState } from 'react'
import { Pressable, Text, TextInput, View, type TextInputProps } from 'react-native'
import { Eye, EyeOff } from 'lucide-react-native'

import { colors } from '@/lib/theme'

interface InputProps extends TextInputProps {
  label?: string
  error?: string
  helper?: string
  required?: boolean
}

export const Input = forwardRef<TextInput, InputProps>(function Input(
  { label, error, helper, required, secureTextEntry, ...props },
  ref
) {
  // Para campos de contraseña: ojito para ver/ocultar lo que se escribe.
  const isPassword = !!secureTextEntry
  const [hidden, setHidden] = useState(true)

  return (
    <View className="gap-1.5">
      {label ? (
        <Text className="text-sm font-medium text-brand">
          {label}
          {required ? <Text className="text-danger"> *</Text> : null}
        </Text>
      ) : null}

      <View className="relative justify-center">
        <TextInput
          ref={ref}
          placeholderTextColor={colors.mutedFg}
          secureTextEntry={isPassword ? hidden : false}
          className={`min-h-[52px] rounded-xl border bg-white px-4 py-3 text-base text-brand ${
            isPassword ? 'pr-12' : ''
          } ${error ? 'border-danger' : 'border-line'}`}
          {...props}
        />
        {isPassword ? (
          <Pressable
            onPress={() => setHidden((h) => !h)}
            hitSlop={10}
            accessibilityRole="button"
            accessibilityLabel={hidden ? 'Mostrar contraseña' : 'Ocultar contraseña'}
            className="absolute right-3 h-11 w-11 items-center justify-center"
          >
            {hidden ? (
              <Eye size={20} color={colors.muted} />
            ) : (
              <EyeOff size={20} color={colors.muted} />
            )}
          </Pressable>
        ) : null}
      </View>

      {error ? (
        <Text className="text-sm text-danger" accessibilityLiveRegion="polite">
          {error}
        </Text>
      ) : helper ? (
        <Text className="text-xs text-muted">{helper}</Text>
      ) : null}
    </View>
  )
})
