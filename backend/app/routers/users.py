"""User management router — admin CRUD (CU-23)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import Role, User
from app.schemas.user import UserCreate, UserListResponse, UserOut, UserUpdate
from app.services.exceptions import ConflictError, NotFoundError, ValidationError
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])

user_service = UserService()


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permisos insuficientes"
        )
    return current_user


@router.get("", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    role: str | None = Query(None),
    search: str | None = Query(None),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> UserListResponse:
    items, total = await user_service.list_users(
        db,
        tenant_id=current_user.tenant_id,
        page=page,
        limit=limit,
        role=role,
        search=search,
    )
    return UserListResponse(
        items=[UserOut.model_validate(u) for u in items],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/{user_id}", response_model=UserOut)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    try:
        user = await user_service.get_user(
            db, user_id=user_id, tenant_id=current_user.tenant_id
        )
        return UserOut.model_validate(user)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", status_code=status.HTTP_201_CREATED, response_model=UserOut)
async def create_user(
    body: UserCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    try:
        user = await user_service.create_user(
            db,
            tenant_id=current_user.tenant_id,
            email=body.email,
            password=body.password,
            full_name=body.full_name,
            role=body.role,
        )
        await db.commit()
        return UserOut.model_validate(user)
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: UUID,
    body: UserUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    try:
        user = await user_service.update_user(
            db,
            user_id=user_id,
            tenant_id=current_user.tenant_id,
            full_name=body.full_name,
            role=body.role,
            is_active=body.is_active,
            password=body.password,
        )
        await db.commit()
        return UserOut.model_validate(user)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
