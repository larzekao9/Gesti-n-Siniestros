"""Claim router — CU-10, CU-14, CU-15, CU-17, CU-30."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.claim import (
    ClaimCreate,
    ClaimListResponse,
    ClaimOut,
    ClaimStatusUpdate,
    PolicyholderSnippet,
    PolicySnippet,
    VehicleSnippet,
)
from app.schemas.observation import (
    ObservationCreate,
    ObservationListResponse,
    ObservationOut,
)
from app.schemas.third_party import (
    ThirdPartyCreate,
    ThirdPartyListResponse,
    ThirdPartyOut,
    ThirdPartyUpdate,
)
from app.services.claim_service import ClaimService
from app.services.observation_service import ObservationService
from app.services.third_party_service import ThirdPartyService
from app.services.exceptions import (
    ConflictError,
    InvalidStateTransitionError,
    NotFoundError,
    PermissionError,
    ValidationError,
)

router = APIRouter(prefix="/claims", tags=["claims"])
claim_service = ClaimService()
observation_service = ObservationService()
third_party_service = ThirdPartyService()


# ── Claim CRUD ─────────────────────────────────────────────────────

@router.get("", response_model=ClaimListResponse)
async def list_claims(
    q: str | None = Query(None),
    status: str | None = Query(None, alias="status"),
    from_date: str | None = Query(None, alias="from"),
    to_date: str | None = Query(None, alias="to"),
    analyst: str | None = Query(None, alias="analyst"),
    policyholder: str | None = Query(None, alias="policyholder"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        from datetime import date
        fd = date.fromisoformat(from_date) if from_date else None
        td = date.fromisoformat(to_date) if to_date else None

        items, total = await claim_service.search(
            db,
            tenant_id=current_user.tenant_id,
            q=q,
            status=status,
            from_date=fd,
            to_date=td,
            analyst_id=analyst,
            policyholder_id=policyholder,
            page=page,
            limit=limit,
        )
        return ClaimListResponse(
            items=[ClaimOut.model_validate(c) for c in items],
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


@router.get("/{claim_id}", response_model=ClaimOut)
async def get_claim(
    claim_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        claim, ph, pol, veh = await claim_service.get_claim_with_related(
            db, claim_id=claim_id, tenant_id=current_user.tenant_id
        )
        out = ClaimOut.model_validate(claim)
        if ph is not None:
            out.policyholder = PolicyholderSnippet.model_validate(ph)
        if pol is not None:
            out.policy = PolicySnippet.model_validate(pol)
        if veh is not None:
            out.vehicle = VehicleSnippet.model_validate(veh)
        return out
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=ClaimOut, status_code=status.HTTP_201_CREATED)
async def create_claim(
    payload: ClaimCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        claim = await claim_service.create_internal(
            db,
            tenant_id=current_user.tenant_id,
            policyholder_id=payload.policyholder_id,
            policy_id=payload.policy_id,
            vehicle_id=payload.vehicle_id,
            accident_date=payload.accident_date,
            accident_time=payload.accident_time,
            accident_location=payload.accident_location,
            accident_lat=payload.accident_lat,
            accident_lng=payload.accident_lng,
            accident_description=payload.accident_description,
            reported_damages=payload.reported_damages,
            actor_user_id=current_user.id,
        )
        await db.commit()
        return ClaimOut.model_validate(claim)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.patch("/{claim_id}/status", response_model=ClaimOut)
async def update_claim_status(
    claim_id: UUID,
    payload: ClaimStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        claim = await claim_service.update_status(
            db,
            claim_id=claim_id,
            tenant_id=current_user.tenant_id,
            new_status=payload.new_status,
            reason=payload.reason,
            actor_user_id=current_user.id,
        )
        await db.commit()
        return ClaimOut.model_validate(claim)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


# ── Observations (sub-resource of claims) ───────────────────────────

@router.get("/{claim_id}/observations", response_model=ObservationListResponse)
async def list_observations(
    claim_id: UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        items, total = await observation_service.list_for_claim(
            db,
            tenant_id=current_user.tenant_id,
            claim_id=claim_id,
            page=page,
            limit=limit,
        )
        return ObservationListResponse(
            items=[ObservationOut.model_validate(o) for o in items],
            total=total,
            page=page,
            limit=limit,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{claim_id}/observations", response_model=ObservationOut, status_code=status.HTTP_201_CREATED)
async def create_observation(
    claim_id: UUID,
    payload: ObservationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        obs = await observation_service.create(
            db,
            tenant_id=current_user.tenant_id,
            claim_id=claim_id,
            comment=payload.comment,
            is_internal=payload.is_internal,
            actor_user_id=current_user.id,
        )
        await db.commit()
        return ObservationOut.model_validate(obs)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


# ── Third Parties (sub-resource of claims) ──────────────────────────

@router.get("/{claim_id}/third-parties", response_model=ThirdPartyListResponse)
async def list_third_parties(
    claim_id: UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        items, total = await third_party_service.list_for_claim(
            db,
            tenant_id=current_user.tenant_id,
            claim_id=claim_id,
            page=page,
            limit=limit,
        )
        return ThirdPartyListResponse(
            items=[ThirdPartyOut.model_validate(t) for t in items],
            total=total,
            page=page,
            limit=limit,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{claim_id}/third-parties", response_model=ThirdPartyOut, status_code=status.HTTP_201_CREATED)
async def create_third_party(
    claim_id: UUID,
    payload: ThirdPartyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        tp = await third_party_service.create(
            db,
            tenant_id=current_user.tenant_id,
            claim_id=claim_id,
            kind=payload.kind,
            full_name=payload.full_name,
            document_id=payload.document_id,
            contact_phone=payload.contact_phone,
            vehicle_plate=payload.vehicle_plate,
            vehicle_info=payload.vehicle_info,
            statement=payload.statement,
            actor_user_id=current_user.id,
        )
        await db.commit()
        return ThirdPartyOut.model_validate(tp)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.put("/{claim_id}/third-parties/{tp_id}", response_model=ThirdPartyOut)
async def update_third_party(
    claim_id: UUID,
    tp_id: UUID,
    payload: ThirdPartyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        tp = await third_party_service.update(
            db,
            third_party_id=tp_id,
            tenant_id=current_user.tenant_id,
            kind=payload.kind,
            full_name=payload.full_name,
            document_id=payload.document_id,
            contact_phone=payload.contact_phone,
            vehicle_plate=payload.vehicle_plate,
            vehicle_info=payload.vehicle_info,
            statement=payload.statement,
            actor_user_id=current_user.id,
        )
        await db.commit()
        return ThirdPartyOut.model_validate(tp)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.delete("/{claim_id}/third-parties/{tp_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_third_party(
    claim_id: UUID,
    tp_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await third_party_service.delete(
            db,
            third_party_id=tp_id,
            tenant_id=current_user.tenant_id,
            actor_user_id=current_user.id,
        )
        await db.commit()
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
