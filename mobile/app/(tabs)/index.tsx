import { FlatList, RefreshControl, Text, View } from 'react-native'
import { useRouter } from 'expo-router'
import { FileText, Plus } from 'lucide-react-native'

import { Button } from '@/components/ui/Button'
import { EmptyState } from '@/components/ui/EmptyState'
import { Loading } from '@/components/ui/Loading'
import { Screen } from '@/components/ui/Screen'
import { ReclamoCard } from '@/components/claim-requests/ReclamoCard'
import { useMyClaimRequests } from '@/lib/hooks/useClaims'
import type { InsuredClaimRequestListItem } from '@/types/claim-request'

export default function HomeScreen() {
  const router = useRouter()
  const { data, isLoading, isRefetching, refetch } = useMyClaimRequests()

  function openItem(item: InsuredClaimRequestListItem) {
    if (item.status === 'draft') {
      router.push(`/reportar/${item.id}/accidente`)
    } else if (item.formalized_claim_id) {
      router.push(`/reclamo/${item.formalized_claim_id}`)
    } else {
      router.push(`/solicitud/${item.id}`)
    }
  }

  if (isLoading) return <Loading label="Cargando tus reclamos…" />

  const items = data?.items ?? []

  return (
    <Screen edges={['top']}>
      <View className="flex-row items-center justify-between px-5 pb-2 pt-3">
        <View>
          <Text className="text-2xl font-bold text-brand">Mis reclamos</Text>
          <Text className="text-sm text-muted">
            {items.length} {items.length === 1 ? 'reclamo' : 'reclamos'}
          </Text>
        </View>
      </View>

      {items.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="Todavía no tenés reclamos"
          description="Cuando reportes un siniestro vas a poder seguir su estado acá."
        >
          <Button
            label="Reportar un siniestro"
            icon={Plus}
            onPress={() => router.push('/(tabs)/reportar')}
          />
        </EmptyState>
      ) : (
        <FlatList
          data={items}
          keyExtractor={(it) => it.id}
          contentContainerStyle={{ padding: 20, paddingTop: 8, gap: 12 }}
          renderItem={({ item }) => (
            <ReclamoCard item={item} onPress={() => openItem(item)} />
          )}
          refreshControl={
            <RefreshControl refreshing={isRefetching} onRefresh={refetch} />
          }
        />
      )}
    </Screen>
  )
}
