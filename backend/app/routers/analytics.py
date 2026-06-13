"""Analytics router — CU-21 operational dashboard endpoints."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import require_role
from app.models.user import Role, User
from app.schemas.analytics import (
    AIKPIsResponse,
    AnalystProductivityResponse,
    CoverageDistributionResponse,
    KPIsResponse,
    StatusDistributionResponse,
    TimelineResponse,
)
from app.services.analytics_service import analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/ai-kpis", response_model=AIKPIsResponse)
async def ai_kpis(
    current_user: User = require_role(Role.SUPERVISOR, Role.ADMIN),
    db: AsyncSession = Depends(get_db),
) -> AIKPIsResponse:
    """Fase 2 de CU-21 (Ciclo 8): KPIs de IA del dashboard."""
    data = await analytics_service.ai_kpis(db, tenant_id=current_user.tenant_id)
    return AIKPIsResponse(**data)


@router.get("/kpis", response_model=KPIsResponse)
async def get_kpis(
    from_: date | None = Query(None, alias="from"),
    to: date | None = Query(None),
    analyst: str | None = Query(None),
    current_user: User = require_role(Role.SUPERVISOR, Role.ADMIN),
    db: AsyncSession = Depends(get_db),
) -> KPIsResponse:
    data = await analytics_service.get_kpis(
        db,
        tenant_id=current_user.tenant_id,
        from_date=from_,
        to_date=to,
        analyst_id=analyst,
    )
    return KPIsResponse(**data)


@router.get("/status-distribution", response_model=StatusDistributionResponse)
async def status_distribution(
    from_: date | None = Query(None, alias="from"),
    to: date | None = Query(None),
    analyst: str | None = Query(None),
    current_user: User = require_role(Role.SUPERVISOR, Role.ADMIN),
    db: AsyncSession = Depends(get_db),
) -> StatusDistributionResponse:
    items, total = await analytics_service.status_distribution(
        db,
        tenant_id=current_user.tenant_id,
        from_date=from_,
        to_date=to,
        analyst_id=analyst,
    )
    return StatusDistributionResponse(items=items, total=total)


@router.get("/timeline", response_model=TimelineResponse)
async def timeline(
    from_: date | None = Query(None, alias="from"),
    to: date | None = Query(None),
    analyst: str | None = Query(None),
    current_user: User = require_role(Role.SUPERVISOR, Role.ADMIN),
    db: AsyncSession = Depends(get_db),
) -> TimelineResponse:
    items = await analytics_service.timeline(
        db,
        tenant_id=current_user.tenant_id,
        from_date=from_,
        to_date=to,
        analyst_id=analyst,
    )
    return TimelineResponse(items=items)


@router.get("/coverage-distribution", response_model=CoverageDistributionResponse)
async def coverage_distribution(
    current_user: User = require_role(Role.SUPERVISOR, Role.ADMIN),
    db: AsyncSession = Depends(get_db),
) -> CoverageDistributionResponse:
    items, total = await analytics_service.coverage_distribution(
        db, tenant_id=current_user.tenant_id
    )
    return CoverageDistributionResponse(items=items, total=total)


@router.get("/analyst-productivity", response_model=AnalystProductivityResponse)
async def analyst_productivity(
    from_: date | None = Query(None, alias="from"),
    to: date | None = Query(None),
    current_user: User = require_role(Role.SUPERVISOR, Role.ADMIN),
    db: AsyncSession = Depends(get_db),
) -> AnalystProductivityResponse:
    items = await analytics_service.analyst_productivity(
        db,
        tenant_id=current_user.tenant_id,
        from_date=from_,
        to_date=to,
    )
    return AnalystProductivityResponse(items=items)
