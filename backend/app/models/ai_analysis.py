"""AI analysis ORM models — Ciclo 8 (CU-32/CU-33).

`ai_analyses` guarda el resultado de cada análisis automático sobre un
expediente (o sobre una solicitud, para el damage_assessment del canal
asegurado — CU-33). `claim_embeddings` persiste el vector pgvector usado
por la detección de duplicados (ADR-011).
"""

from __future__ import annotations

import enum
from decimal import Decimal
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    CheckConstraint,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    JSON,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, TimestampMixin

# 1536 = dimensión de text-embedding-3-small (settings.OPENAI_EMBEDDING_MODEL).
EMBEDDING_DIM = 1536

# En Postgres es vector(1536) nativo; en SQLite (tests) degrada a JSON y la
# similitud se calcula en Python (fallback de DuplicateDetectionService).
EmbeddingColumn = Vector(EMBEDDING_DIM).with_variant(JSON(), "sqlite")


class AIAnalysisKind(str, enum.Enum):
    INCONSISTENCY = "inconsistency"
    DUPLICATE = "duplicate"
    FRAUD_SCORE = "fraud_score"
    DAMAGE_ASSESSMENT = "damage_assessment"


class AIAnalysisStatus(str, enum.Enum):
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"


class AIAnalysis(TenantMixin, TimestampMixin, Base):
    """Resultado de un análisis IA sobre un claim o claim_request."""

    __tablename__ = "ai_analyses"
    __table_args__ = (
        # Igual que evidences: el análisis pertenece a un claim O a un
        # claim_request (CU-33 corre sobre el draft, antes de formalizar).
        CheckConstraint(
            "claim_id IS NOT NULL OR claim_request_id IS NOT NULL",
            name="ck_ai_analyses_subject_must_exist",
        ),
        Index("ix_ai_analyses_tenant_claim", "tenant_id", "claim_id"),
        Index("ix_ai_analyses_tenant_request", "tenant_id", "claim_request_id"),
        Index("ix_ai_analyses_tenant_kind", "tenant_id", "kind"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    # SET NULL para conservar historial de análisis (Context.md §2.2.5).
    claim_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("claims.id", ondelete="SET NULL"), nullable=True
    )
    claim_request_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("claim_requests.id", ondelete="SET NULL"), nullable=True
    )
    # Evidencia analizada (solo kind=damage_assessment, CU-33).
    evidence_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("evidences.id", ondelete="SET NULL"), nullable=True
    )
    kind: Mapped[AIAnalysisKind] = mapped_column(
        SQLEnum(AIAnalysisKind, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    status: Mapped[AIAnalysisStatus] = mapped_column(
        SQLEnum(AIAnalysisStatus, values_callable=lambda x: [e.value for e in x]),
        default=AIAnalysisStatus.PROCESSING,
        nullable=False,
    )
    score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    # Contrato por kind (Context.md §6 Ciclo 8):
    #   inconsistency      → {"findings": [{"severity", "field", "message"}]}
    #   duplicate          → {"matches": [{"claim_id", "claim_number", "similarity"}]}
    #   fraud_score        → {"score", "factors": [{"name", "contribution", "direction"}]}
    #   damage_assessment  → {"damage_type", "severity", "confidence"}
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(100), nullable=True)


class ClaimEmbedding(TenantMixin, TimestampMixin, Base):
    """Embedding del texto de un claim, para similitud coseno (duplicados)."""

    __tablename__ = "claim_embeddings"
    __table_args__ = (
        Index("ix_claim_embeddings_claim", "claim_id", unique=True),
        Index("ix_claim_embeddings_tenant", "tenant_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    claim_id: Mapped[UUID] = mapped_column(
        ForeignKey("claims.id", ondelete="CASCADE"), nullable=False
    )
    embedding: Mapped[list[float]] = mapped_column(EmbeddingColumn, nullable=False)
    # Hash del texto fuente para evitar re-embeddear contenido sin cambios.
    source_text_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    model_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
