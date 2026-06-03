"""Pydantic schemas for notifications."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    recipient_user_id: UUID | None
    recipient_account_id: UUID | None
    entity_type: str
    entity_id: UUID | None
    kind: str
    title: str
    body: str
    read_at: datetime | None
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime | None


class NotificationListResponse(BaseModel):
    items: list[NotificationOut]
    total: int
    page: int
    limit: int
    unread_count: int
