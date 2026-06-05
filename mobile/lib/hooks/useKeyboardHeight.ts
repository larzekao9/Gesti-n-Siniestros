import { useEffect, useState } from 'react'
import { Keyboard, Platform } from 'react-native'

// Altura real del teclado (0 si está oculto). Fiable en cualquier teléfono y
// compatible con Expo Go / edge-to-edge (no depende de KeyboardAvoidingView).
export function useKeyboardHeight(): number {
  const [height, setHeight] = useState(0)

  useEffect(() => {
    const showEvt = Platform.OS === 'ios' ? 'keyboardWillShow' : 'keyboardDidShow'
    const hideEvt = Platform.OS === 'ios' ? 'keyboardWillHide' : 'keyboardDidHide'
    const show = Keyboard.addListener(showEvt, (e) =>
      setHeight(e.endCoordinates?.height ?? 0)
    )
    const hide = Keyboard.addListener(hideEvt, () => setHeight(0))
    return () => {
      show.remove()
      hide.remove()
    }
  }, [])

  return height
}
