"""Policyholder CRUD router (CU-11)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.user import Role, User
from app.schemas.insured_auth import InviteResponse
from app.schemas.policyholder import (
    PolicyholderCreate,
    PolicyholderListResponse,
    PolicyholderOut,
    PolicyholderUpdate,
)
from app.services.exceptions import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.services.insured_auth_service import insured_auth_service
from app.services.policyholder_service import PolicyholderService

router = APIRouter(prefix="/policyholders", tags=["policyholders"])

service = PolicyholderService()


@router.get("", response_model=PolicyholderListResponse)
async def list_policyholders(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PolicyholderListResponse:
    items, total = await service.list_policyholders(
        db, tenant_id=current_user.tenant_id, page=page, limit=limit, search=search
    )
    return PolicyholderListResponse(
        items=[PolicyholderOut.model_validate(p) for p in items],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/{policyholder_id}", response_model=PolicyholderOut)
async def get_policyholder(
    policyholder_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PolicyholderOut:
    try:
        ph = await service.get_policyholder(
            db, policyholder_id=policyholder_id, tenant_id=current_user.tenant_id
        )
        return PolicyholderOut.model_validate(ph)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", status_code=status.HTTP_201_CREATED, response_model=PolicyholderOut)
async def create_policyholder(
    body: PolicyholderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PolicyholderOut:
    try:
        ph = await service.create_policyholder(
            db,
            tenant_id=current_user.tenant_id,
            document_id=body.document_id,
            full_name=body.full_name,
            phone=body.phone,
            email=body.email,
            address=body.address,
        )
        await db.commit()
        return PolicyholderOut.model_validate(ph)
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/{policyholder_id}/invite", response_model=InviteResponse)
async def invite_policyholder(
    policyholder_id: UUID,
    current_user: User = require_role(Role.ADMIN, Role.SUPERVISOR, Role.ANALYST),
    db: AsyncSession = Depends(get_db),
) -> InviteResponse:
    """Genera el activation_token para que el asegurado registre su cuenta (CU-01 F-A1).

    Cualquier rol interno puede invitar. NO envía mail: el token se devuelve en la
    respuesta para que el analista lo comparta por el canal que corresponda.
    """
    try:
        account = await insured_auth_service.create_invitation(
            db,
            policyholder_id=policyholder_id,
            tenant_id=current_user.tenant_id,
            actor_user_id=current_user.id,
        )
        await db.commit()
        return InviteResponse(
            account_id=account.id,
            activation_token=account.activation_token,
            activation_expires_at=account.activation_expires_at.isoformat(),
            email=account.email,
        )
    except NotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValidationError as e:
        await db.rollback()
        raise HTTPException(status_code=422, detail=str(e))


@router.patch("/{policyholder_id}", response_model=PolicyholderOut)
async def update_policyholder(
    policyholder_id: UUID,
    body: PolicyholderUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PolicyholderOut:
    try:
        ph = await service.update_policyholder(
            db,
            policyholder_id=policyholder_id,
            tenant_id=current_user.tenant_id,
            full_name=body.full_name,
            phone=body.phone,
            email=body.email,
            address=body.address,
            status=body.status,
        )
        await db.commit()
        return PolicyholderOut.model_validate(ph)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
