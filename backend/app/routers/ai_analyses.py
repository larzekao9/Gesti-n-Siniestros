"""AI analyses router — CU-32: consultar resultado del análisis inteligente.

GET  /api/claims/{id}/ai-analyses          → último análisis por kind.
POST /api/claims/{id}/ai-analyses/refresh  → re-ejecuta (supervisor/admin).
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.ai_analysis import AIAnalysis
from app.models.user import Role, User
from app.schemas.ai_analysis import (
    AIAnalysisListResponse,
    AIAnalysisOut,
    AIRefreshResponse,
)
from app.services.claim_service import ClaimService
from app.services.exceptions import NotFoundError

router = APIRouter(prefix="/claims", tags=["ai-analyses"])
claim_service = ClaimService()


@router.get("/{claim_id}/ai-analyses", response_model=AIAnalysisListResponse)
async def list_ai_analyses(
    claim_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        # Valida tenant + existencia (cross-tenant → 404).
        await claim_service.get_claim(
            db, claim_id=claim_id, tenant_id=current_user.tenant_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    rows = (
        await db.execute(
            select(AIAnalysis)
            .where(
                AIAnalysis.claim_id == claim_id,
                AIAnalysis.tenant_id == current_user.tenant_id,
            )
            .order_by(AIAnalysis.created_at.desc())
        )
    ).scalars()

    # El más reciente por kind (las corridas anteriores quedan como historial).
    latest: dict[str, AIAnalysis] = {}
    for row in rows:
        latest.setdefault(row.kind.value, row)

    return AIAnalysisListResponse(
        items=[AIAnalysisOut.model_validate(a) for a in latest.values()]
    )


@router.post(
    "/{claim_id}/ai-analyses/refresh",
    response_model=AIRefreshResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def refresh_ai_analyses(
    claim_id: UUID,
    current_user: User = require_role(Role.SUPERVISOR, Role.ADMIN),
    db: AsyncSession = Depends(get_db),
):
    try:
        await claim_service.get_claim(
            db, claim_id=claim_id, tenant_id=current_user.tenant_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    from app.tasks.ai_analysis import enqueue_claim_ai_analysis

    enqueued = enqueue_claim_ai_analysis(current_user.tenant_id, claim_id)
    if not enqueued:
        raise HTTPException(
            status_code=503,
            detail="No se pudo encolar el análisis (worker no disponible)",
        )
    return AIRefreshResponse(detail="Análisis encolado", enqueued=True)
