import Constants from 'expo-constants'

// Base URL del backend. En dev apunta a localhost; para probar en un dispositivo
// real usá la IP de tu máquina o un túnel (ngrok). Se puede sobreescribir con la
// env var EXPO_PUBLIC_API_BASE_URL sin recompilar.
const fromExtra =
  (Constants.expoConfig?.extra as { apiBaseUrl?: string } | undefined)?.apiBaseUrl

export const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_BASE_URL ?? fromExtra ?? 'http://localhost:8000/api'

// Claves de almacenamiento seguro (expo-secure-store).
export const SECURE_KEYS = {
  refreshToken: 'insured_refresh_token',
} as const
