"""Policyholder (asegurado) ORM model."""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, TimestampMixin


class Policyholder(TenantMixin, TimestampMixin, Base):
    """A person insured under the tenant."""

    __tablename__ = "policyholders"
    __table_args__ = (
        Index("ix_policyholders_tenant_document", "tenant_id", "document_id", unique=True),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    document_id: Mapped[str] = mapped_column(String(20), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
