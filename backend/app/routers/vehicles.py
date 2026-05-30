"""Vehicle CRUD router (CU-13)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.vehicle import VehicleCreate, VehicleListResponse, VehicleOut, VehicleUpdate
from app.services.exceptions import ConflictError, NotFoundError, ValidationError
from app.services.vehicle_service import VehicleService

router = APIRouter(prefix="/vehicles", tags=["vehicles"])

service = VehicleService()


@router.get("", response_model=VehicleListResponse)
async def list_vehicles(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    policy_id: UUID | None = Query(None),
    search: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VehicleListResponse:
    items, total = await service.list_vehicles(
        db,
        tenant_id=current_user.tenant_id,
        page=page,
        limit=limit,
        policy_id=policy_id,
        search=search,
    )
    return VehicleListResponse(
        items=[VehicleOut.model_validate(v) for v in items],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/{vehicle_id}", response_model=VehicleOut)
async def get_vehicle(
    vehicle_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VehicleOut:
    try:
        vehicle = await service.get_vehicle(
            db, vehicle_id=vehicle_id, tenant_id=current_user.tenant_id
        )
        return VehicleOut.model_validate(vehicle)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", status_code=status.HTTP_201_CREATED, response_model=VehicleOut)
async def create_vehicle(
    body: VehicleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VehicleOut:
    try:
        vehicle = await service.create_vehicle(
            db,
            tenant_id=current_user.tenant_id,
            plate=body.plate,
            make=body.make,
            model=body.model,
            year=body.year,
            color=body.color,
            vehicle_type=body.vehicle_type,
            policy_id=body.policy_id,
        )
        await db.commit()
        return VehicleOut.model_validate(vehicle)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.patch("/{vehicle_id}", response_model=VehicleOut)
async def update_vehicle(
    vehicle_id: UUID,
    body: VehicleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VehicleOut:
    try:
        vehicle = await service.update_vehicle(
            db,
            vehicle_id=vehicle_id,
            tenant_id=current_user.tenant_id,
            make=body.make,
            model=body.model,
            year=body.year,
            color=body.color,
            vehicle_type=body.vehicle_type,
            policy_id=body.policy_id,
            status=body.status,
        )
        await db.commit()
        return VehicleOut.model_validate(vehicle)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
