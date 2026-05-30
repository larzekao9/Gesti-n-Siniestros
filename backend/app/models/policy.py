"""Policy (póliza) ORM model."""

from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

from sqlalchemy import Date, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, TimestampMixin


class Policy(TenantMixin, TimestampMixin, Base):
    """An insurance policy linked to a policyholder."""

    __tablename__ = "policies"
    __table_args__ = (
        Index("ix_policies_tenant_number", "tenant_id", "policy_number", unique=True),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    policy_number: Mapped[str] = mapped_column(String(50), nullable=False)
    policyholder_id: Mapped[UUID] = mapped_column(
        ForeignKey("policyholders.id", ondelete="CASCADE"), nullable=False
    )
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date] = mapped_column(Date, nullable=False)
    coverage_type: Mapped[str] = mapped_column(String(100), nullable=False)
    exclusions: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
