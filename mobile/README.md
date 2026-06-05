# Siniestros — App del Asegurado (Ciclo 7)

App móvil nativa (**React Native + Expo SDK 54**, ADR-008) para el **canal del asegurado**.
> Nota: se fijó SDK **54** (no 56) porque el Expo Go publicado en la Play Store todavía
> no soporta 56. SDK 54 ya corre en Expo Go sin dev build.
Cubre CU-01..CU-08: acceder, reportar un siniestro con cámara y GPS, enviar la
solicitud, seguir el estado del reclamo y adjuntar documentación solicitada.

> Es un proyecto **independiente** dentro de `Gesti-n-Siniestros/`. **No** va en Docker
> (el backend y el panel web sí). Consume la API del backend FastAPI (`/api/insured-auth/*`
> y `/api/me/*`).

## Stack

| Área | Tecnología |
|---|---|
| Framework | Expo SDK 54 (managed) · expo-router (file-based) |
| Estilos | NativeWind 4 (Tailwind) · paleta "Trust & Authority" (navy + verde) |
| Tipografía | IBM Plex Sans (`@expo-google-fonts/ibm-plex-sans`) |
| Estado / datos | Zustand · TanStack Query · axios (interceptor + refresh rotativo) |
| Formularios | react-hook-form + zod |
| Auth storage | `expo-secure-store` (refresh token en Keychain/KeyStore; access token en memoria) |
| Multimedia / GPS / Push | expo-camera · expo-image-picker · expo-location · expo-notifications |
| Iconos | lucide-react-native |

## Estructura

```
app/                       # rutas (expo-router)
  _layout.tsx              # providers + fuentes + guard de sesión
  (auth)/                  # login, register (token de activación), forgot-password  [CU-01]
  (tabs)/                  # Mis reclamos · Reportar · Avisos · Perfil
  reportar/[requestId]/    # wizard: accidente (+GPS) · evidencias · confirmar       [CU-02..05]
  reclamo/[id].tsx         # expediente formalizado + docs pendientes + timeline      [CU-06/07/08]
  solicitud/[id].tsx       # detalle de solicitud (en revisión / rechazada)           [CU-06]
components/                # ui/ (Button, Input, Card, StatusBadge, OptionPicker…) + claim-requests/
lib/
  api/                     # client (axios+refresh) + insured-auth, claim-requests, evidences, notifications, catalog
  stores/authStore.ts      # Zustand + expo-secure-store
  hooks/                   # TanStack Query + usePushToken + useBootstrap
  validations/             # Zod (espejo del patrón de /frontend)
  theme.ts                 # tokens de color + estilos de estado
types/                     # ★ espejo de /frontend/types
```

## Configuración del backend (API)

La app apunta por defecto a `http://localhost:8000/api` (ver `app.json → extra.apiBaseUrl`).
Para probar en un **dispositivo real**, el `localhost` del teléfono no es tu PC: usá la IP
de tu máquina o un túnel. Podés sobrescribir sin recompilar:

```bash
EXPO_PUBLIC_API_BASE_URL="http://192.168.0.10:8000/api" npx expo start
# o un túnel:
EXPO_PUBLIC_API_BASE_URL="https://<tu-subdominio>.ngrok.io/api" npx expo start --tunnel
```

## Cómo correrlo (dev)

```bash
cd Gesti-n-Siniestros/mobile
npm install
npx expo start            # escaneá el QR con Expo Go (Android/iOS)
# o:
npx expo start --android  # emulador Android
```

> Si las versiones de paquetes Expo no coinciden con el SDK instalado, corré
> `npx expo install --fix` una vez.

### Flujo de prueba end-to-end

1. **Backend levantado** (`docker compose up -d`) y con datos (`make seed` o creando
   asegurado + póliza + vehículo desde el panel web).
2. Desde el **panel web** (analista/admin): abrir el asegurado y **"Invitar"**
   (`POST /api/policyholders/{id}/invite`) → copia el `activation_token` que devuelve.
3. En la app: **Activá tu cuenta** → pegá el token → fijá contraseña → entrás.
4. **Reportar** → elegí vehículo/póliza → datos del accidente (con GPS) → tomá fotos →
   **Enviar**. Recibís el número `REQ-...`.
5. El analista la **toma** y **formaliza** (o **rechaza**) desde el web → te llega una
   **notificación push** y aparece en "Avisos".
6. Si te **piden documentación**, entrá al expediente y **adjuntá** desde "Mis reclamos".

## Build con EAS (APK para el docente)

`eas.json` trae 3 perfiles: `development`, `preview`, `production`.

```bash
npm install -g eas-cli      # una vez (fuera de Docker; herramienta de usuario)
eas login
eas build:configure          # genera/asocia el projectId (actualiza app.json → extra.eas.projectId)
eas build --platform android --profile preview   # → genera un APK descargable
```

> El comando imprime un **link** de descarga del APK. El docente lo instala en cualquier
> Android (Opción B). Para iOS se requiere cuenta de Apple Developer (opcional).

### Cómo prueba el entregable el docente

- **Opción A (recomendada):** instalar **Expo Go** y escanear el QR de `npx expo start`
  apuntando al backend (localhost con `--tunnel`/ngrok, o desplegado).
- **Opción B:** descargar e instalar el **APK** generado por `eas build --profile preview`.

## Tests

```bash
npm test          # jest-expo + @testing-library/react-native
npm run typecheck # tsc --noEmit
```

Cubre validaciones Zod, mapeo de estados/formato y un smoke test de `StatusBadge`.

## Notas de diseño (accesibilidad)

- Touch targets ≥ 44pt, estados de carga en cada acción async, errores junto al campo.
- Color **nunca** es el único indicador (los badges de estado llevan dot + texto).
- Safe areas respetadas (`react-native-safe-area-context`); tab bar ≤ 5 ítems.
- El asegurado **nunca** ve `fraud_score`, datos internos del staff ni observaciones
  `is_internal=true` (lo garantiza el schema dedicado `ClaimOutInsured` del backend).

## Sincronización de tipos

`types/` y `lib/validations/` son **copia** de `/frontend` (decisión pragmática §6.7.3 de
`Context.md`). Mantener sincronizado vía PR review al cambiar contratos del backend.
