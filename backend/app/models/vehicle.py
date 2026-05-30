"""Vehicle ORM model."""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, TimestampMixin


class Vehicle(TenantMixin, TimestampMixin, Base):
    """A vehicle covered by a policy."""

    __tablename__ = "vehicles"
    __table_args__ = (
        Index("ix_vehicles_tenant_plate", "tenant_id", "plate", unique=True),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    plate: Mapped[str] = mapped_column(String(20), nullable=False)
    make: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(50), nullable=False)
    year: Mapped[int] = mapped_column(nullable=False)
    color: Mapped[str | None] = mapped_column(String(30), nullable=True)
    vehicle_type: Mapped[str] = mapped_column(String(50), default="sedan")
    policy_id: Mapped[UUID] = mapped_column(
        ForeignKey("policies.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), default="active")
