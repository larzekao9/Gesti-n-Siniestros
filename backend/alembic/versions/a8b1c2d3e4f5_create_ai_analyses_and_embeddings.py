"""create_ai_analyses_and_embeddings (Ciclo 8)

- Extensión pgvector (ADR-011) para similitud coseno de duplicados.
- Tabla ai_analyses: resultados de inconsistency/duplicate/fraud_score/
  damage_assessment con status processing/done/error.
- Tabla claim_embeddings: vector(1536) por claim.
- Nuevo valor 'ai_alert' en notificationkind (alerta de fraude alto).

Revision ID: a8b1c2d3e4f5
Revises: d7a3c9e1f5b2
Create Date: 2026-06-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "a8b1c2d3e4f5"
down_revision: Union[str, None] = "d7a3c9e1f5b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIM = 1536


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "ai_analyses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("claim_id", sa.Uuid(), nullable=True),
        sa.Column("claim_request_id", sa.Uuid(), nullable=True),
        sa.Column("evidence_id", sa.Uuid(), nullable=True),
        sa.Column(
            "kind",
            sa.Enum(
                "inconsistency",
                "duplicate",
                "fraud_score",
                "damage_assessment",
                name="aianalysiskind",
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("processing", "done", "error", name="aianalysisstatus"),
            nullable=False,
        ),
        sa.Column("score", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("model_version", sa.String(length=100), nullable=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "claim_id IS NOT NULL OR claim_request_id IS NOT NULL",
            name="ck_ai_analyses_subject_must_exist",
        ),
        sa.ForeignKeyConstraint(["claim_id"], ["claims.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["claim_request_id"], ["claim_requests.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["evidence_id"], ["evidences.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_analyses_tenant_claim", "ai_analyses", ["tenant_id", "claim_id"])
    op.create_index("ix_ai_analyses_tenant_request", "ai_analyses", ["tenant_id", "claim_request_id"])
    op.create_index("ix_ai_analyses_tenant_kind", "ai_analyses", ["tenant_id", "kind"])
    op.create_index(op.f("ix_ai_analyses_tenant_id"), "ai_analyses", ["tenant_id"])

    op.create_table(
        "claim_embeddings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("claim_id", sa.Uuid(), nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=False),
        sa.Column("source_text_hash", sa.String(length=64), nullable=False),
        sa.Column("model_version", sa.String(length=100), nullable=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["claim_id"], ["claims.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_claim_embeddings_claim", "claim_embeddings", ["claim_id"], unique=True)
    op.create_index("ix_claim_embeddings_tenant", "claim_embeddings", ["tenant_id"])
    op.create_index(op.f("ix_claim_embeddings_tenant_id"), "claim_embeddings", ["tenant_id"])

    # PG12+: permitido dentro de transacción mientras el valor nuevo no se use
    # en la misma transacción (acá solo se declara).
    op.execute("ALTER TYPE notificationkind ADD VALUE IF NOT EXISTS 'ai_alert'")


def downgrade() -> None:
    op.drop_index(op.f("ix_claim_embeddings_tenant_id"), table_name="claim_embeddings")
    op.drop_index("ix_claim_embeddings_tenant", table_name="claim_embeddings")
    op.drop_index("ix_claim_embeddings_claim", table_name="claim_embeddings")
    op.drop_table("claim_embeddings")
    op.drop_index(op.f("ix_ai_analyses_tenant_id"), table_name="ai_analyses")
    op.drop_index("ix_ai_analyses_tenant_kind", table_name="ai_analyses")
    op.drop_index("ix_ai_analyses_tenant_request", table_name="ai_analyses")
    op.drop_index("ix_ai_analyses_tenant_claim", table_name="ai_analyses")
    op.drop_table("ai_analyses")
    sa.Enum(name="aianalysiskind").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="aianalysisstatus").drop(op.get_bind(), checkfirst=True)
    # 'ai_alert' queda en notificationkind: PG no soporta DROP VALUE y es inocuo.
    # La extensión vector no se borra (podría estar en uso por otros objetos).
