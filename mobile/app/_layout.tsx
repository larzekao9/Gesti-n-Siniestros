import '../global.css'

import { useEffect } from 'react'
import { GestureHandlerRootView } from 'react-native-gesture-handler'
import { SafeAreaProvider } from 'react-native-safe-area-context'
import { StatusBar } from 'expo-status-bar'
import { Stack, useRouter, useSegments } from 'expo-router'
import * as SplashScreen from 'expo-splash-screen'
import { QueryClientProvider } from '@tanstack/react-query'
import {
  useFonts,
  IBMPlexSans_400Regular,
  IBMPlexSans_500Medium,
  IBMPlexSans_600SemiBold,
  IBMPlexSans_700Bold,
} from '@expo-google-fonts/ibm-plex-sans'

import { queryClient } from '@/lib/queryClient'
import { useAuthStore } from '@/lib/stores/authStore'
import { useBootstrap } from '@/lib/hooks/useBootstrap'

SplashScreen.preventAutoHideAsync().catch(() => {})

function RootNavigator() {
  const { ready } = useBootstrap()
  const account = useAuthStore((s) => s.account)
  const segments = useSegments()
  const router = useRouter()

  const [fontsLoaded] = useFonts({
    IBMPlexSans_400Regular,
    IBMPlexSans_500Medium,
    IBMPlexSans_600SemiBold,
    IBMPlexSans_700Bold,
  })

  // Guard de rutas: redirige según haya o no sesión, una vez listo el bootstrap.
  useEffect(() => {
    if (!ready) return
    const inAuthGroup = segments[0] === '(auth)'
    if (!account && !inAuthGroup) {
      router.replace('/(auth)/login')
    } else if (account && inAuthGroup) {
      router.replace('/(tabs)')
    }
  }, [ready, account, segments, router])

  useEffect(() => {
    if (ready && fontsLoaded) {
      SplashScreen.hideAsync().catch(() => {})
    }
  }, [ready, fontsLoaded])

  if (!ready || !fontsLoaded) return null

  return (
    <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: '#F8FAFC' } }}>
      <Stack.Screen name="index" />
      <Stack.Screen name="(auth)" />
      <Stack.Screen name="(tabs)" />
      <Stack.Screen name="reportar/[requestId]" options={{ presentation: 'card' }} />
      <Stack.Screen
        name="reclamo/[id]"
        options={{
          headerShown: true,
          title: 'Mi reclamo',
          headerStyle: { backgroundColor: '#0F172A' },
          headerTintColor: '#FFFFFF',
        }}
      />
      <Stack.Screen
        name="solicitud/[id]"
        options={{
          headerShown: true,
          title: 'Solicitud',
          headerStyle: { backgroundColor: '#0F172A' },
          headerTintColor: '#FFFFFF',
        }}
      />
    </Stack>
  )
}

export default function RootLayout() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <QueryClientProvider client={queryClient}>
          <StatusBar style="light" />
          <RootNavigator />
        </QueryClientProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  )
}
