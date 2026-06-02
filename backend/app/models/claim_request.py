"""Claim request (solicitud / FNOL) ORM model."""

from __future__ import annotations

import enum
from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Date, Enum as SQLEnum, ForeignKey, Index, String, Text, Time, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, TimestampMixin


class ClaimRequestStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_INTAKE_REVIEW = "under_intake_review"
    FORMALIZED = "formalized"
    REJECTED_AT_INTAKE = "rejected_at_intake"


class ClaimRequest(TenantMixin, TimestampMixin, Base):
    """A claim request submitted by the insured via the mobile app."""

    __tablename__ = "claim_requests"
    __table_args__ = (
        Index("ix_claim_requests_tenant_number", "tenant_id", "request_number", unique=True),
        Index("ix_claim_requests_tenant_status", "tenant_id", "status"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    request_number: Mapped[str | None] = mapped_column(String(30), nullable=True)
    status: Mapped[ClaimRequestStatus] = mapped_column(
        SQLEnum(ClaimRequestStatus, values_callable=lambda x: [e.value for e in x]),
        default=ClaimRequestStatus.DRAFT,
        nullable=False,
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
    accident_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    accident_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    accident_location: Mapped[str | None] = mapped_column(String(500), nullable=True)
    accident_lat: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    accident_lng: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    accident_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    reported_damages: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(nullable=True)
    reviewed_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    intake_decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    formalized_claim_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("claims.id", ondelete="SET NULL", use_alter=True), nullable=True
    )
