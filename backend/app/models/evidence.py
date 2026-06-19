"""Evidence ORM model."""

from __future__ import annotations

import enum
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Enum as SQLEnum, ForeignKey, Index, Integer, String, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, TimestampMixin


class EvidenceType(str, enum.Enum):
    PHOTO = "photo"
    VIDEO = "video"
    INVOICE = "invoice"
    TECHNICAL_REPORT = "technical_report"
    SKETCH = "sketch"
    POLICE_REPORT = "police_report"
    PERSONAL_DOC = "personal_doc"
    OTHER = "other"


class Evidence(TenantMixin, TimestampMixin, Base):
    """Multimedia evidence attached to a claim_request or claim."""

    __tablename__ = "evidences"
    __table_args__ = (
        CheckConstraint(
            "claim_request_id IS NOT NULL OR claim_id IS NOT NULL",
            name="ck_evidences_subject_must_exist",
        ),
        Index("ix_evidences_tenant_claim", "tenant_id", "claim_id"),
        Index("ix_evidences_tenant_request", "tenant_id", "claim_request_id"),
        Index("ix_evidences_tenant_doc_request", "tenant_id", "document_request_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    claim_request_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("claim_requests.id", ondelete="CASCADE"), nullable=True
    )
    claim_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("claims.id", ondelete="CASCADE"), nullable=True
    )
    type: Mapped[EvidenceType] = mapped_column(
        SQLEnum(EvidenceType, values_callable=lambda x: [e.value for e in x]),
        default=EvidenceType.OTHER,
        nullable=False,
    )
    file_url: Mapped[str] = mapped_column(String(1000), nullable=False, comment="S3 key")
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata", JSON, nullable=True, comment="Peritaje fields, EXIF, OCR, etc."
    )
    uploaded_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    # Evidencia subida por el asegurado desde la app móvil (Ciclo 7).
    uploaded_by_account_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("policyholder_accounts.id", ondelete="SET NULL"), nullable=True
    )
    document_request_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("document_requests.id", ondelete="SET NULL"), nullable=True
    )
