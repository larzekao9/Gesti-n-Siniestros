"""Policy CRUD router (CU-12)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.policy import PolicyCreate, PolicyListResponse, PolicyOut, PolicyUpdate
from app.services.exceptions import ConflictError, NotFoundError, ValidationError
from app.services.policy_service import PolicyService

router = APIRouter(prefix="/policies", tags=["policies"])

service = PolicyService()


@router.get("", response_model=PolicyListResponse)
async def list_policies(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    policyholder_id: UUID | None = Query(None),
    search: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PolicyListResponse:
    items, total = await service.list_policies(
        db,
        tenant_id=current_user.tenant_id,
        page=page,
        limit=limit,
        policyholder_id=policyholder_id,
        search=search,
    )
    return PolicyListResponse(
        items=[PolicyOut.model_validate(p) for p in items],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/{policy_id}", response_model=PolicyOut)
async def get_policy(
    policy_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PolicyOut:
    try:
        policy = await service.get_policy(db, policy_id=policy_id, tenant_id=current_user.tenant_id)
        return PolicyOut.model_validate(policy)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", status_code=status.HTTP_201_CREATED, response_model=PolicyOut)
async def create_policy(
    body: PolicyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PolicyOut:
    try:
        policy = await service.create_policy(
            db,
            tenant_id=current_user.tenant_id,
            policy_number=body.policy_number,
            policyholder_id=body.policyholder_id,
            valid_from=body.valid_from,
            valid_to=body.valid_to,
            coverage_type=body.coverage_type,
            exclusions=body.exclusions,
            actor_user_id=current_user.id,
        )
        await db.commit()
        return PolicyOut.model_validate(policy)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{policy_id}", response_model=PolicyOut)
async def update_policy(
    policy_id: UUID,
    body: PolicyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PolicyOut:
    try:
        policy = await service.update_policy(
            db,
            policy_id=policy_id,
            tenant_id=current_user.tenant_id,
            policy_number=body.policy_number,
            valid_from=body.valid_from,
            valid_to=body.valid_to,
            coverage_type=body.coverage_type,
            exclusions=body.exclusions,
            status=body.status,
            actor_user_id=current_user.id,
        )
        await db.commit()
        return PolicyOut.model_validate(policy)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
