import { FlatList, Pressable, RefreshControl, Text, View } from 'react-native'
import { useRouter } from 'expo-router'
import { Bell, BellOff, CheckCheck } from 'lucide-react-native'

import { Card } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { Loading } from '@/components/ui/Loading'
import { Screen } from '@/components/ui/Screen'
import {
  useMarkAllRead,
  useMarkRead,
  useNotifications,
} from '@/lib/hooks/useNotifications'
import { colors } from '@/lib/theme'
import { relativeTime } from '@/lib/utils/format'
import type { Notification } from '@/types/notification'

export default function NotificacionesScreen() {
  const router = useRouter()
  const { data, isLoading, isRefetching, refetch } = useNotifications()
  const markRead = useMarkRead()
  const markAllRead = useMarkAllRead()

  function onPress(n: Notification) {
    if (!n.read_at) markRead.mutate(n.id)
    if (n.entity_type === 'claim' && n.entity_id) {
      router.push(`/reclamo/${n.entity_id}`)
    } else if (n.entity_type === 'claim_request' && n.entity_id) {
      router.push(`/solicitud/${n.entity_id}`)
    }
  }

  if (isLoading) return <Loading label="Cargando avisos…" />

  const items = data?.items ?? []
  const unread = data?.unread_count ?? 0

  return (
    <Screen edges={['top']}>
      <View className="flex-row items-center justify-between px-5 pb-2 pt-3">
        <View>
          <Text className="text-2xl font-bold text-brand">Avisos</Text>
          <Text className="text-sm text-muted">
            {unread > 0 ? `${unread} sin leer` : 'Estás al día'}
          </Text>
        </View>
        {unread > 0 ? (
          <Pressable
            onPress={() => markAllRead.mutate()}
            hitSlop={8}
            className="flex-row items-center gap-1.5 rounded-full bg-accent-50 px-3 py-2"
            accessibilityLabel="Marcar todo como leído"
          >
            <CheckCheck size={16} color={colors.accent} />
            <Text className="text-xs font-semibold text-accent">Marcar todo</Text>
          </Pressable>
        ) : null}
      </View>

      {items.length === 0 ? (
        <EmptyState
          icon={BellOff}
          title="No tenés avisos"
          description="Te avisaremos cuando haya novedades sobre tus reclamos."
        />
      ) : (
        <FlatList
          data={items}
          keyExtractor={(n) => n.id}
          contentContainerStyle={{ padding: 20, paddingTop: 8, gap: 10 }}
          refreshControl={
            <RefreshControl refreshing={isRefetching} onRefresh={refetch} />
          }
          renderItem={({ item }) => {
            const unreadItem = !item.read_at
            return (
              <Card onPress={() => onPress(item)} className="flex-row gap-3">
                <View
                  className="mt-0.5 h-9 w-9 items-center justify-center rounded-full"
                  style={{ backgroundColor: unreadItem ? colors.accent50 : colors.background }}
                >
                  <Bell size={18} color={unreadItem ? colors.accent : colors.muted} />
                </View>
                <View className="flex-1">
                  <View className="flex-row items-center gap-2">
                    <Text
                      className={`flex-1 text-base ${unreadItem ? 'font-bold text-brand' : 'font-medium text-brand'}`}
                      numberOfLines={1}
                    >
                      {item.title}
                    </Text>
                    {unreadItem ? (
                      <View className="h-2 w-2 rounded-full bg-accent" />
                    ) : null}
                  </View>
                  <Text className="mt-0.5 text-sm leading-5 text-muted">{item.body}</Text>
                  <Text className="mt-1 text-xs text-muted-fg">
                    {relativeTime(item.created_at)}
                  </Text>
                </View>
              </Card>
            )
          }}
        />
      )}
    </Screen>
  )
}
