"""Tenant (aseguradora) ORM model."""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Tenant(TimestampMixin, Base):
    """Represents an insurance company tenant in the multi-tenant system."""

    __tablename__ = "tenants"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    is_active: Mapped[bool] = mapped_column(default=True)
    subscription_plan: Mapped[str] = mapped_column(String(50), default="basic")

    users: Mapped[list["User"]] = relationship(  # noqa: F821
        back_populates="tenant",
        cascade="all, delete-orphan",
    )
