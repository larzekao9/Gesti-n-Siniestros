"""State transition audit model."""

from __future__ import annotations

import enum
from uuid import UUID, uuid4

from sqlalchemy import Enum as SQLEnum, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, TimestampMixin


class SubjectType(str, enum.Enum):
    CLAIM_REQUEST = "claim_request"
    CLAIM = "claim"


class StateTransition(TenantMixin, TimestampMixin, Base):
    """Audit record of a state change in either state machine."""

    __tablename__ = "state_transitions"
    __table_args__ = (
        Index("ix_state_transitions_subject", "tenant_id", "subject_type", "subject_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    subject_type: Mapped[SubjectType] = mapped_column(
        SQLEnum(SubjectType), nullable=False
    )
    subject_id: Mapped[UUID] = mapped_column(nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    to_status: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    actor_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
