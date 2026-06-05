"""Device token ORM model — push notifications via Expo (CU-27 canal asegurado)."""

from __future__ import annotations

import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, TimestampMixin


class DevicePlatform(str, enum.Enum):
    IOS = "ios"
    ANDROID = "android"


class DeviceToken(TenantMixin, TimestampMixin, Base):
    """Expo push token de un dispositivo del asegurado.

    Un asegurado puede tener N dispositivos (celular + tablet). Se usa para
    despachar push notifications via Expo Push API cuando se crea una
    ``notification`` con ``recipient_account_id``.
    """

    __tablename__ = "device_tokens"
    __table_args__ = (
        Index("ix_device_tokens_expo_token", "expo_push_token", unique=True),
        Index("ix_device_tokens_tenant_account", "tenant_id", "account_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("policyholder_accounts.id", ondelete="CASCADE"), nullable=False
    )
    expo_push_token: Mapped[str] = mapped_column(String(255), nullable=False)
    platform: Mapped[DevicePlatform] = mapped_column(
        SQLEnum(DevicePlatform, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
