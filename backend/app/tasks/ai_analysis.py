"""Celery task del análisis IA — Ciclo 8.

Se dispara cuando un claim pasa a `in_evaluation` (CU-15 / CU-19) o vía
`POST /api/claims/{id}/ai-analyses/refresh` (CU-32). Corre los tres análisis
(inconsistencias LLM, duplicados pgvector, fraude heurístico) y deja cada
resultado en su fila de `ai_analyses` con status done/error independiente:
si OpenAI falla, el heurístico de fraude (sin IO) igual completa.

⚠1/⚠2 (Context.md §6 Ciclo 8): la task recibe `tenant_id` y `claim_id`
EXPLÍCITOS (no hay middleware de tenant acá) y usa `task_session()` —
engine async propio por invocación, ver app/tasks/db.py.
"""

import logging
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select

from app.core.celery_app import celery_app
from app.core.config import settings
from app.tasks.db import run_async, task_session

logger = logging.getLogger(__name__)


def enqueue_claim_ai_analysis(tenant_id, claim_id) -> bool:
    """Encola el análisis best-effort: si el broker está caído, la operación
    de negocio (cambio de estado) NO se rompe. countdown=2 deja que el
    request que disparó la transición commitee antes de que el worker lea."""
    try:
        run_claim_ai_analysis.apply_async(
            args=[str(tenant_id), str(claim_id)], countdown=2
        )
        return True
    except Exception as e:
        logger.warning("No se pudo encolar el análisis IA para claim %s: %s", claim_id, e)
        return False


@celery_app.task(name="run_claim_ai_analysis")
def run_claim_ai_analysis(tenant_id: str, claim_id: str) -> dict:
    return run_async(_run_all(UUID(tenant_id), UUID(claim_id)))


async def _run_all(tenant_id: UUID, claim_id: UUID) -> dict:
    from app.models.ai_analysis import AIAnalysis, AIAnalysisKind, AIAnalysisStatus
    from app.services.ai.claim_context import load_claim_context
    from app.services.ai.duplicate_service import duplicate_service
    from app.services.ai.embedding_service import embedding_service
    from app.services.ai.fraud_score_service import fraud_score_service
    from app.services.ai.inconsistency_service import inconsistency_service

    def _apply(row: AIAnalysis, result: dict, model_version: str | None) -> None:
        row.score = (
            Decimal(str(result["score"])) if result.get("score") is not None else None
        )
        row.payload = result["payload"]
        row.explanation = result["explanation"]
        row.model_version = model_version
        row.status = AIAnalysisStatus.DONE

    def _fail(row: AIAnalysis, error: Exception) -> None:
        row.status = AIAnalysisStatus.ERROR
        row.explanation = "El análisis falló. Reintentá con 'Re-ejecutar análisis'."
        row.payload = {"error": str(error)[:300]}

    async with task_session() as db:
        ctx = await load_claim_context(db, claim_id=claim_id, tenant_id=tenant_id)

        # Una fila nueva por kind y por corrida (la UI muestra la más reciente;
        # las anteriores quedan como historial).
        rows = {
            kind: AIAnalysis(
                tenant_id=tenant_id,
                claim_id=claim_id,
                kind=kind,
                status=AIAnalysisStatus.PROCESSING,
            )
            for kind in (
                AIAnalysisKind.INCONSISTENCY,
                AIAnalysisKind.DUPLICATE,
                AIAnalysisKind.FRAUD_SCORE,
            )
        }
        for row in rows.values():
            db.add(row)
        # Commit temprano: el polling de la UI (F-A1) ve "processing" ya.
        await db.commit()

        # 1) Inconsistencias (LLM)
        try:
            result = await inconsistency_service.analyze(db, ctx=ctx)
            _apply(rows[AIAnalysisKind.INCONSISTENCY], result, settings.OPENAI_CHAT_MODEL)
        except Exception as e:
            logger.warning("Análisis de inconsistencias falló (claim %s): %s", claim_id, e)
            _fail(rows[AIAnalysisKind.INCONSISTENCY], e)
        await db.commit()

        # 2) Duplicados (embedding + pgvector)
        duplicate_top_similarity = None
        try:
            embedding = await embedding_service.upsert_claim_embedding(db, ctx=ctx)
            result = await duplicate_service.analyze(
                db, ctx=ctx, embedding=embedding.embedding
            )
            duplicate_top_similarity = result.get("top_similarity")
            _apply(rows[AIAnalysisKind.DUPLICATE], result, settings.OPENAI_EMBEDDING_MODEL)
        except Exception as e:
            logger.warning("Detección de duplicados falló (claim %s): %s", claim_id, e)
            _fail(rows[AIAnalysisKind.DUPLICATE], e)
        await db.commit()

        # 3) Fraude (heurístico, sin IO — ADR-010). Usa el resultado de
        # duplicados si está disponible.
        try:
            result = fraud_score_service.compute(
                ctx=ctx, duplicate_top_similarity=duplicate_top_similarity
            )
            _apply(rows[AIAnalysisKind.FRAUD_SCORE], result, "heuristic-v1")
            ctx.claim.fraud_score = Decimal(str(result["score"]))
            if result["score"] > settings.AI_FRAUD_ALERT_THRESHOLD:
                await _notify_supervisors(db, ctx=ctx, score=result["score"])
        except Exception as e:
            logger.warning("Fraud score falló (claim %s): %s", claim_id, e)
            _fail(rows[AIAnalysisKind.FRAUD_SCORE], e)
        await db.commit()

        return {
            "claim_id": str(claim_id),
            "statuses": {k.value: rows[k].status.value for k in rows},
        }


async def _notify_supervisors(db, *, ctx, score: float) -> None:
    """F-A3: fraude alto → notificación al supervisor. Si el expediente no
    fue escalado todavía (supervisor_id NULL), avisa a todos los supervisores
    activos del tenant (fallback: admins)."""
    from app.models.notification import NotificationKind
    from app.models.user import Role, User
    from app.services.notification_service import notification_service

    claim = ctx.claim
    if claim.supervisor_id is not None:
        recipient_ids = [claim.supervisor_id]
    else:
        result = await db.execute(
            select(User.id).where(
                User.tenant_id == claim.tenant_id,
                User.role == Role.SUPERVISOR,
                User.is_active.is_(True),
            )
        )
        recipient_ids = [row[0] for row in result.all()]
        if not recipient_ids:
            result = await db.execute(
                select(User.id).where(
                    User.tenant_id == claim.tenant_id,
                    User.role == Role.ADMIN,
                    User.is_active.is_(True),
                )
            )
            recipient_ids = [row[0] for row in result.all()]

    for user_id in recipient_ids:
        await notification_service.create(
            db,
            tenant_id=claim.tenant_id,
            recipient_user_id=user_id,
            entity_type="claim",
            entity_id=claim.id,
            kind=NotificationKind.AI_ALERT,
            title="Alerta de riesgo de fraude",
            body=(
                f"El expediente {claim.claim_number} tiene un score de fraude "
                f"de {score:.2f} (umbral {settings.AI_FRAUD_ALERT_THRESHOLD:.2f})."
            ),
        )
