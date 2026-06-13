"""DuplicateDetectionService — similitud coseno con pgvector (ADR-011).

Contrato del payload (Context.md §6 Ciclo 8):
    {"matches": [{"claim_id", "claim_number", "similarity"}]}

En Postgres usa el operador ``<=>`` (cosine_distance) de pgvector.
En SQLite (tests) degrada a un cálculo de coseno en Python sobre los
embeddings del tenant — mismo resultado, sin SQL vectorial.
"""

import math
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.ai_analysis import ClaimEmbedding
from app.models.claim import Claim
from app.services.ai.claim_context import ClaimContext

_TOP_K = 5


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if not norm_a or not norm_b:
        return 0.0
    return dot / (norm_a * norm_b)


class DuplicateDetectionService:
    async def analyze(
        self, db: AsyncSession, *, ctx: ClaimContext, embedding
    ) -> dict:
        tenant_id = ctx.claim.tenant_id
        dialect = db.bind.dialect.name if db.bind is not None else "sqlite"

        if dialect == "postgresql":
            distance = ClaimEmbedding.embedding.cosine_distance(embedding)
            rows = (
                await db.execute(
                    select(ClaimEmbedding.claim_id, distance.label("distance"))
                    .where(
                        ClaimEmbedding.tenant_id == tenant_id,
                        ClaimEmbedding.claim_id != ctx.claim.id,
                    )
                    .order_by(distance)
                    .limit(_TOP_K)
                )
            ).all()
            pairs: list[tuple[UUID, float]] = [
                (row.claim_id, 1.0 - float(row.distance)) for row in rows
            ]
        else:
            # Fallback Python (tests SQLite): los embeddings degradan a JSON.
            rows = (
                await db.execute(
                    select(ClaimEmbedding).where(
                        ClaimEmbedding.tenant_id == tenant_id,
                        ClaimEmbedding.claim_id != ctx.claim.id,
                    )
                )
            ).scalars()
            query_vec = list(embedding)
            pairs = sorted(
                (
                    (e.claim_id, _cosine_similarity(query_vec, list(e.embedding)))
                    for e in rows
                ),
                key=lambda p: p[1],
                reverse=True,
            )[:_TOP_K]

        top_similarity = pairs[0][1] if pairs else None
        threshold = settings.AI_DUPLICATE_THRESHOLD
        flagged = [(cid, sim) for cid, sim in pairs if sim >= threshold]

        # Resolver claim_numbers de los flaggeados (siempre dentro del tenant).
        matches = []
        if flagged:
            ids = [cid for cid, _ in flagged]
            number_rows = (
                await db.execute(
                    select(Claim.id, Claim.claim_number).where(
                        Claim.tenant_id == tenant_id, Claim.id.in_(ids)
                    )
                )
            ).all()
            numbers = {row.id: row.claim_number for row in number_rows}
            matches = [
                {
                    "claim_id": str(cid),
                    "claim_number": numbers.get(cid, "?"),
                    "similarity": round(sim, 4),
                }
                for cid, sim in flagged
            ]

        if matches:
            explanation = (
                f"Se detectaron {len(matches)} expediente(s) con similitud ≥ "
                f"{threshold:.2f}: posible duplicado o siniestro repetido."
            )
        else:
            explanation = "No se encontraron expedientes similares por encima del umbral."

        return {
            "score": round(top_similarity, 4) if top_similarity is not None else None,
            "payload": {"matches": matches},
            "explanation": explanation,
            "top_similarity": top_similarity,
        }


duplicate_service = DuplicateDetectionService()
