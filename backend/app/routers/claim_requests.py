"""Claim request router — CU-24, CU-25, CU-30."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import Role, User
from app.schemas.claim_request import (
    ClaimRequestListResponse,
    ClaimRequestOut,
    ReassignPayload,
    RejectIntakePayload,
)
from app.schemas.claim import FormalizeResponse, ClaimOut
from app.services.claim_request_service import ClaimRequestService
from app.services.claim_service import ClaimService
from app.services.exceptions import (
    ConflictError,
    NotFoundError,
    PermissionError,
    ValidationError,
)

router = APIRouter(prefix="/claim-requests", tags=["claim-requests"])
claim_request_service = ClaimRequestService()
claim_service = ClaimService()


@router.get("", response_model=ClaimRequestListResponse)
async def list_claim_requests(
    q: str | None = Query(None, description="Search by number, location, description"),
    status: str | None = Query(None, alias="status"),
    from_date: str | None = Query(None, alias="from"),
    to_date: str | None = Query(None, alias="to"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        from datetime import date
        fd = date.fromisoformat(from_date) if from_date else None
        td = date.fromisoformat(to_date) if to_date else None

        items, total = await claim_request_service.search(
            db,
            tenant_id=current_user.tenant_id,
            q=q,
            status=status,
            from_date=fd,
            to_date=td,
            page=page,
            limit=limit,
        )
        return ClaimRequestListResponse(
            items=[ClaimRequestOut.model_validate(r) for r in items],
            total=total,
            page=page,
            limit=limit,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{request_id}", response_model=ClaimRequestOut)
async def get_claim_request(
    request_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        cr = await claim_request_service.get_request(
            db, request_id=request_id, tenant_id=current_user.tenant_id
        )
        return ClaimRequestOut.model_validate(cr)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{request_id}/take", response_model=ClaimRequestOut)
async def take_request(
    request_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        cr = await claim_request_service.take(
            db,
            request_id=request_id,
            tenant_id=current_user.tenant_id,
            actor_user_id=current_user.id,
        )
        await db.commit()
        return ClaimRequestOut.model_validate(cr)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/{request_id}/release", response_model=ClaimRequestOut)
async def release_request(
    request_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        cr = await claim_request_service.release(
            db,
            request_id=request_id,
            tenant_id=current_user.tenant_id,
            actor_user_id=current_user.id,
        )
        await db.commit()
        return ClaimRequestOut.model_validate(cr)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/{request_id}/reassign", response_model=ClaimRequestOut)
async def reassign_request(
    request_id: UUID,
    payload: ReassignPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Solo administradores pueden reasignar")
    try:
        cr = await claim_request_service.reassign(
            db,
            request_id=request_id,
            tenant_id=current_user.tenant_id,
            target_user_id=payload.target_user_id,
            actor_user_id=current_user.id,
        )
        await db.commit()
        return ClaimRequestOut.model_validate(cr)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/{request_id}/reject", response_model=ClaimRequestOut)
async def reject_request(
    request_id: UUID,
    payload: RejectIntakePayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        cr = await claim_request_service.reject_at_intake(
            db,
            request_id=request_id,
            tenant_id=current_user.tenant_id,
            reason=payload.reason,
            actor_user_id=current_user.id,
        )
        await db.commit()
        return ClaimRequestOut.model_validate(cr)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/{request_id}/formalize", response_model=FormalizeResponse)
async def formalize_request(
    request_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        claim, req = await claim_service.formalize_request(
            db,
            request_id=request_id,
            tenant_id=current_user.tenant_id,
            actor_user_id=current_user.id,
        )
        await db.commit()
        return FormalizeResponse(
            claim=ClaimOut.model_validate(claim),
            request=ClaimRequestOut.model_validate(req),
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
