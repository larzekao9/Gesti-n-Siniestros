"""Traffic report ORM model."""

from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

from sqlalchemy import Date, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, TimestampMixin


class TrafficReport(TenantMixin, TimestampMixin, Base):
    """Structured traffic / police report information attached to a claim."""

    __tablename__ = "traffic_reports"
    __table_args__ = (
        Index("ix_traffic_reports_tenant_claim", "tenant_id", "claim_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    claim_id: Mapped[UUID] = mapped_column(
        ForeignKey("claims.id", ondelete="CASCADE"), nullable=False
    )
    evidence_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("evidences.id", ondelete="SET NULL"), nullable=True,
        comment="Archivo del acta subido como evidencia (type=police_report)"
    )
    officer_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    report_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    jurisdiction: Mapped[str | None] = mapped_column(String(200), nullable=True)
    report_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
