"""Document request ORM model."""

from __future__ import annotations

import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Enum as SQLEnum, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, TimestampMixin


class DocumentRequestStatus(str, enum.Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    WAIVED = "waived"


class DocumentRequest(TenantMixin, TimestampMixin, Base):
    """A request for the insured to provide additional documentation."""

    __tablename__ = "document_requests"
    __table_args__ = (
        Index("ix_doc_requests_tenant_claim", "tenant_id", "claim_id"),
        Index("ix_doc_requests_tenant_status", "tenant_id", "status"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    claim_id: Mapped[UUID] = mapped_column(
        ForeignKey("claims.id", ondelete="CASCADE"), nullable=False
    )
    requested_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[DocumentRequestStatus] = mapped_column(
        SQLEnum(DocumentRequestStatus, values_callable=lambda x: [e.value for e in x]),
        default=DocumentRequestStatus.PENDING,
        nullable=False,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(nullable=True)
