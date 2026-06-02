"""Claim (expediente) ORM model."""

from __future__ import annotations

import enum
from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Date, Enum as SQLEnum, ForeignKey, Index, String, Text, Time, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, TimestampMixin


class ClaimStatus(str, enum.Enum):
    REGISTERED = "registered"
    IN_REVIEW = "in_review"
    OBSERVED = "observed"
    DOCS_PENDING = "docs_pending"
    IN_EVALUATION = "in_evaluation"
    APPROVED = "approved"
    REJECTED = "rejected"
    CLOSED = "closed"


class ClaimSource(str, enum.Enum):
    MOBILE_APP = "mobile_app"
    INTERNAL = "internal"


class ClaimDecision(str, enum.Enum):
    APPROVED = "approved"
    REJECTED = "rejected"


class Claim(TenantMixin, TimestampMixin, Base):
    """A formal claim file (expediente)."""

    __tablename__ = "claims"
    __table_args__ = (
        Index("ix_claims_tenant_number", "tenant_id", "claim_number", unique=True),
        Index("ix_claims_tenant_status", "tenant_id", "status"),
        Index("ix_claims_tenant_analyst", "tenant_id", "assigned_analyst_id"),
        Index("ix_claims_tenant_supervisor", "tenant_id", "supervisor_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    claim_number: Mapped[str] = mapped_column(String(30), nullable=False)
    claim_request_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("claim_requests.id", ondelete="SET NULL"), nullable=True, unique=True
    )
    policyholder_id: Mapped[UUID] = mapped_column(
        ForeignKey("policyholders.id", ondelete="CASCADE"), nullable=False
    )
    policy_id: Mapped[UUID] = mapped_column(
        ForeignKey("policies.id", ondelete="CASCADE"), nullable=False
    )
    vehicle_id: Mapped[UUID] = mapped_column(
        ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[ClaimStatus] = mapped_column(
        SQLEnum(ClaimStatus, values_callable=lambda x: [e.value for e in x]),
        default=ClaimStatus.REGISTERED,
        nullable=False,
    )
    source: Mapped[ClaimSource] = mapped_column(
        SQLEnum(ClaimSource, values_callable=lambda x: [e.value for e in x]),
        default=ClaimSource.INTERNAL,
        nullable=False,
    )
    accident_date: Mapped[date] = mapped_column(Date, nullable=False)
    accident_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    accident_location: Mapped[str] = mapped_column(String(500), nullable=False)
    accident_lat: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    accident_lng: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    accident_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    reported_damages: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    assigned_analyst_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    supervisor_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    fraud_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    decision: Mapped[ClaimDecision | None] = mapped_column(
        SQLEnum(ClaimDecision, values_callable=lambda x: [e.value for e in x]),
        nullable=True,
    )
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    decided_at: Mapped[datetime | None] = mapped_column(nullable=True)
