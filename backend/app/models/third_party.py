"""Third party ORM model."""

from __future__ import annotations

import enum
from uuid import UUID, uuid4

from sqlalchemy import Enum as SQLEnum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, TimestampMixin


class ThirdPartyKind(str, enum.Enum):
    DRIVER = "driver"
    WITNESS = "witness"
    VICTIM = "victim"
    VEHICLE_OWNER = "vehicle_owner"


class ThirdParty(TenantMixin, TimestampMixin, Base):
    """A third party involved in a claim."""

    __tablename__ = "third_parties"
    __table_args__ = (
        Index("ix_third_parties_tenant_claim", "tenant_id", "claim_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    claim_id: Mapped[UUID] = mapped_column(
        ForeignKey("claims.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[ThirdPartyKind] = mapped_column(
        SQLEnum(ThirdPartyKind, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    document_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    vehicle_plate: Mapped[str | None] = mapped_column(String(20), nullable=True)
    vehicle_info: Mapped[str | None] = mapped_column(String(200), nullable=True)
    statement: Mapped[str | None] = mapped_column(Text, nullable=True)
