"""Notification model for internal user and insured notifications."""

from __future__ import annotations

import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, TimestampMixin


class NotificationKind(str, enum.Enum):
    INTAKE_REJECTED = "intake_rejected"
    DOCS_REQUESTED = "docs_requested"
    ESCALATED = "escalated"
    ASSIGNED = "assigned"
    DECISION = "decision"
    STATE_CHANGE = "state_change"
    CLAIM_CREATED = "claim_created"


class Notification(TenantMixin, TimestampMixin, Base):
    """Notification for a user or insured account."""

    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_tenant_recipient", "tenant_id", "recipient_user_id"),
        Index("ix_notifications_tenant_account", "tenant_id", "recipient_account_id"),
        Index("ix_notifications_tenant_entity", "tenant_id", "entity_type", "entity_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    recipient_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    # TODO Ciclo 7: add ForeignKey("policyholder_accounts.id", ondelete="CASCADE")
    recipient_account_id: Mapped[UUID | None] = mapped_column(nullable=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[UUID | None] = mapped_column(nullable=True)
    kind: Mapped[NotificationKind] = mapped_column(
        SQLEnum(NotificationKind, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
