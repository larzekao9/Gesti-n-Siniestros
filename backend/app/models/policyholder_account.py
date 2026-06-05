"""Policyholder account ORM model — login del asegurado en la app móvil (Ciclo 7)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, TimestampMixin


class PolicyholderAccount(TenantMixin, TimestampMixin, Base):
    """Cuenta del asegurado para autenticarse en la app móvil (CU-01).

    Se crea vía invitación: el analista genera un ``activation_token`` al invitar
    a un policyholder (``POST /api/policyholders/{id}/invite``). El asegurado fija
    su contraseña con ese token (``register-with-token``), lo que activa la cuenta.
    """

    __tablename__ = "policyholder_accounts"
    __table_args__ = (
        Index(
            "ix_policyholder_accounts_tenant_email",
            "tenant_id",
            "email",
            unique=True,
        ),
        Index(
            "ix_policyholder_accounts_activation_token",
            "activation_token",
            unique=True,
        ),
        Index(
            "ix_policyholder_accounts_reset_token",
            "password_reset_token",
            unique=True,
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    policyholder_id: Mapped[UUID] = mapped_column(
        ForeignKey("policyholders.id", ondelete="CASCADE"), nullable=False
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    # Nullable hasta que el asegurado fija su contraseña con el activation_token.
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Invitación / activación (single-use, con expiración).
    activation_token: Mapped[str | None] = mapped_column(String(64), nullable=True)
    activation_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Restablecimiento de contraseña (single-use, con expiración).
    password_reset_token: Mapped[str | None] = mapped_column(String(64), nullable=True)
    password_reset_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # MFA: columnas presentes por fidelidad al modelo (Context §2.2.1); el flujo
    # MFA del canal asegurado NO se implementa en el Ciclo 7 (decisión del usuario).
    mfa_secret: Mapped[str | None] = mapped_column(String(32), nullable=True)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
