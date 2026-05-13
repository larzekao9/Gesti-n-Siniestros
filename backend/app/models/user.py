"""User ORM model with role-based access control."""

from __future__ import annotations

import enum
from uuid import UUID, uuid4

from sqlalchemy import Enum as SQLEnum, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TenantMixin, TimestampMixin


class Role(str, enum.Enum):
    """Roles available to users within a tenant."""

    ADMIN = "admin"
    SUPERVISOR = "supervisor"
    ANALYST = "analyst"


class User(TenantMixin, TimestampMixin, Base):
    """A user account scoped to a specific tenant."""

    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_tenant_email", "tenant_id", "email"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[Role] = mapped_column(SQLEnum(Role), default=Role.ANALYST)
    is_active: Mapped[bool] = mapped_column(default=True)
    mfa_secret: Mapped[str | None] = mapped_column(String(32), nullable=True)
    mfa_enabled: Mapped[bool] = mapped_column(default=False)

    tenant: Mapped["Tenant"] = relationship(back_populates="users")  # noqa: F821
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(  # noqa: F821
        back_populates="user",
        cascade="all, delete-orphan",
    )
