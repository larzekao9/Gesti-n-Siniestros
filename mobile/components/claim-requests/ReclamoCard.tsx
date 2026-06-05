import { Text, View } from 'react-native'
import { ChevronRight, FileText, MapPin } from 'lucide-react-native'

import { Card } from '@/components/ui/Card'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { colors } from '@/lib/theme'
import { formatDate } from '@/lib/utils/format'
import type { InsuredClaimRequestListItem } from '@/types/claim-request'

export function ReclamoCard({
  item,
  onPress,
}: {
  item: InsuredClaimRequestListItem
  onPress: () => void
}) {
  const title = item.request_number ?? 'Borrador sin enviar'
  return (
    <Card onPress={onPress} className="gap-3">
      <View className="flex-row items-start justify-between">
        <View className="flex-row items-center gap-2">
          <View className="h-10 w-10 items-center justify-center rounded-xl bg-accent-50">
            <FileText size={20} color={colors.accent} />
          </View>
          <View>
            <Text className="text-base font-semibold text-brand">{title}</Text>
            <Text className="text-xs text-muted">{formatDate(item.accident_date)}</Text>
          </View>
        </View>
        <ChevronRight size={20} color={colors.mutedFg} />
      </View>

      {item.accident_location ? (
        <View className="flex-row items-center gap-1.5">
          <MapPin size={14} color={colors.muted} />
          <Text className="flex-1 text-sm text-muted" numberOfLines={1}>
            {item.accident_location}
          </Text>
        </View>
      ) : null}

      <View className="flex-row items-center justify-between">
        <StatusBadge status={item.status} />
        {item.formalized_claim_id ? (
          <Text className="text-xs font-medium text-accent">Ver expediente →</Text>
        ) : null}
      </View>
    </Card>
  )
}
