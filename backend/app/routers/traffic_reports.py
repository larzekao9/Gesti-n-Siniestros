"""Traffic report router — CU-16."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.traffic_report import (
    TrafficReportCreate,
    TrafficReportListResponse,
    TrafficReportOut,
    TrafficReportUpdate,
)
from app.services.traffic_report_service import traffic_report_service
from app.services.exceptions import (
    NotFoundError,
    ValidationError,
)

router = APIRouter(prefix="/traffic-reports", tags=["traffic_reports"])


@router.get("", response_model=TrafficReportListResponse)
async def list_for_claim(
    claim_id: UUID = Query(..., alias="claim_id"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await traffic_report_service.list_for_claim(
        db,
        claim_id=claim_id,
        tenant_id=current_user.tenant_id,
        page=page,
        limit=limit,
    )
    return TrafficReportListResponse(
        items=[TrafficReportOut.model_validate(t) for t in items],
        total=total,
        page=page,
        limit=limit,
    )


@router.post("", response_model=TrafficReportOut, status_code=status.HTTP_201_CREATED)
async def create_traffic_report(
    payload: TrafficReportCreate,
    claim_id: UUID = Query(..., alias="claim_id"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        report = await traffic_report_service.create(
            db,
            claim_id=claim_id,
            evidence_id=payload.evidence_id,
            officer_name=payload.officer_name,
            report_code=payload.report_code,
            jurisdiction=payload.jurisdiction,
            report_date=payload.report_date,
            summary=payload.summary,
            tenant_id=current_user.tenant_id,
            actor_user_id=current_user.id,
        )
        await db.commit()
        return TrafficReportOut.model_validate(report)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.put("/{report_id}", response_model=TrafficReportOut)
async def update_traffic_report(
    report_id: UUID,
    payload: TrafficReportUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        report = await traffic_report_service.update(
            db,
            report_id=report_id,
            evidence_id=payload.evidence_id,
            officer_name=payload.officer_name,
            report_code=payload.report_code,
            jurisdiction=payload.jurisdiction,
            report_date=payload.report_date,
            summary=payload.summary,
            tenant_id=current_user.tenant_id,
            actor_user_id=current_user.id,
        )
        await db.commit()
        return TrafficReportOut.model_validate(report)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_traffic_report(
    report_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await traffic_report_service.delete(
            db,
            report_id=report_id,
            tenant_id=current_user.tenant_id,
            actor_user_id=current_user.id,
        )
        await db.commit()
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
