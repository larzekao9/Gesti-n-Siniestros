export interface Notification {
  id: string
  recipient_user_id: string | null
  recipient_account_id: string | null
  entity_type: string
  entity_id: string | null
  kind: string
  title: string
  body: string
  read_at: string | null
  tenant_id: string
  created_at: string
  updated_at: string | null
}

export interface NotificationListResponse {
  items: Notification[]
  total: number
  page: number
  limit: number
  unread_count: number
}
