"""EmbeddingService — genera y persiste embeddings de claims (ADR-011)."""

import hashlib

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.ai_analysis import ClaimEmbedding
from app.services.ai.claim_context import ClaimContext, build_claim_text
from app.services.ai.openai_client import get_openai_client


class EmbeddingService:
    """Embeddings OpenAI persistidos en Postgres vía pgvector."""

    async def embed_text(self, text: str) -> list[float]:
        client = get_openai_client()
        resp = await client.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL,
            input=text[:8000],
        )
        return list(resp.data[0].embedding)

    async def upsert_claim_embedding(
        self, db: AsyncSession, *, ctx: ClaimContext
    ) -> ClaimEmbedding:
        """Crea/actualiza el embedding del claim. Evita re-embeddear si el
        texto fuente no cambió (hash)."""
        text = build_claim_text(ctx)
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

        existing = (
            await db.execute(
                select(ClaimEmbedding).where(ClaimEmbedding.claim_id == ctx.claim.id)
            )
        ).scalar_one_or_none()

        if existing is not None and existing.source_text_hash == text_hash:
            return existing

        vector = await self.embed_text(text)

        if existing is not None:
            existing.embedding = vector
            existing.source_text_hash = text_hash
            existing.model_version = settings.OPENAI_EMBEDDING_MODEL
            await db.flush()
            return existing

        embedding = ClaimEmbedding(
            tenant_id=ctx.claim.tenant_id,
            claim_id=ctx.claim.id,
            embedding=vector,
            source_text_hash=text_hash,
            model_version=settings.OPENAI_EMBEDDING_MODEL,
        )
        db.add(embedding)
        await db.flush()
        return embedding


embedding_service = EmbeddingService()
