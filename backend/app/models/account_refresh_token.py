"""Refresh token del canal asegurado (paralelo a refresh_tokens, Ciclo 7)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, TimestampMixin


class AccountRefreshToken(TenantMixin, TimestampMixin, Base):
    """Refresh token persistido y revocable para una ``policyholder_account``.

    Equivalente a :class:`RefreshToken` pero para el canal asegurado. Se mantiene
    separado para no tocar la auth interna (que ya funciona) — ver Context §2.2.1
    "similar para policyholder_accounts (Ciclo 7)".
    """

    __tablename__ = "account_refresh_tokens"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    token: Mapped[str] = mapped_column(
        String(500), unique=True, nullable=False, index=True
    )
    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("policyholder_accounts.id", ondelete="CASCADE"), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
