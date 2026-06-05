import { Loading } from '@/components/ui/Loading'

// Ruta raíz: el guard del layout (app/_layout.tsx) redirige a (auth) o (tabs)
// según el estado de sesión una vez terminado el bootstrap.
export default function Index() {
  return <Loading label="Cargando…" />
}
