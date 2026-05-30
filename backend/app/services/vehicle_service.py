"""Vehicle domain service."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.policy import Policy
from app.models.vehicle import Vehicle
from app.services.exceptions import ConflictError, NotFoundError, ValidationError


class VehicleService:
    """CRUD for insured vehicles."""

    async def list_vehicles(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        page: int = 1,
        limit: int = 20,
        policy_id: UUID | None = None,
        search: str | None = None,
    ) -> tuple[list[Vehicle], int]:
        offset = (page - 1) * limit
        query = select(Vehicle).where(Vehicle.tenant_id == tenant_id)

        if policy_id:
            query = query.where(Vehicle.policy_id == policy_id)
        if search:
            pattern = f"%{search}%"
            query = query.where(
                (Vehicle.plate.ilike(pattern)) | (Vehicle.make.ilike(pattern)) | (Vehicle.model.ilike(pattern))
            )

        count_q = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_q)).scalar_one()

        query = query.order_by(Vehicle.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all()), total

    async def get_vehicle(
        self, db: AsyncSession, *, vehicle_id: UUID, tenant_id: UUID
    ) -> Vehicle:
        result = await db.execute(
            select(Vehicle).where(Vehicle.id == vehicle_id, Vehicle.tenant_id == tenant_id)
        )
        vehicle = result.scalar_one_or_none()
        if vehicle is None:
            raise NotFoundError("Vehículo no encontrado")
        return vehicle

    async def create_vehicle(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        plate: str,
        make: str,
        model: str,
        year: int,
        color: str | None = None,
        vehicle_type: str = "sedan",
        policy_id: UUID,
    ) -> Vehicle:
        policy_result = await db.execute(
            select(Policy).where(Policy.id == policy_id, Policy.tenant_id == tenant_id)
        )
        policy = policy_result.scalar_one_or_none()
        if policy is None:
            raise NotFoundError("Póliza no encontrada")
        if policy.status != "active":
            raise ValidationError("La póliza no está activa")

        existing = await db.execute(
            select(Vehicle).where(Vehicle.tenant_id == tenant_id, Vehicle.plate == plate)
        )
        if existing.scalar_one_or_none() is not None:
            raise ConflictError("Ya existe un vehículo con esa placa en este tenant")

        vehicle = Vehicle(
            tenant_id=tenant_id,
            plate=plate,
            make=make,
            model=model,
            year=year,
            color=color,
            vehicle_type=vehicle_type,
            policy_id=policy_id,
        )
        db.add(vehicle)
        await db.flush()
        return vehicle

    async def update_vehicle(
        self,
        db: AsyncSession,
        *,
        vehicle_id: UUID,
        tenant_id: UUID,
        make: str | None = None,
        model: str | None = None,
        year: int | None = None,
        color: str | None = None,
        vehicle_type: str | None = None,
        policy_id: UUID | None = None,
        status: str | None = None,
    ) -> Vehicle:
        vehicle = await self.get_vehicle(db, vehicle_id=vehicle_id, tenant_id=tenant_id)

        if policy_id is not None and policy_id != vehicle.policy_id:
            policy_result = await db.execute(
                select(Policy).where(Policy.id == policy_id, Policy.tenant_id == tenant_id)
            )
            if policy_result.scalar_one_or_none() is None:
                raise NotFoundError("Póliza no encontrada")
            vehicle.policy_id = policy_id

        if make is not None:
            vehicle.make = make
        if model is not None:
            vehicle.model = model
        if year is not None:
            vehicle.year = year
        if color is not None:
            vehicle.color = color
        if vehicle_type is not None:
            vehicle.vehicle_type = vehicle_type
        if status is not None:
            vehicle.status = status

        await db.flush()
        await db.refresh(vehicle)
        return vehicle

    async def belongs_to_policy(
        self, db: AsyncSession, *, vehicle_id: UUID, policy_id: UUID
    ) -> bool:
        result = await db.execute(
            select(Vehicle).where(Vehicle.id == vehicle_id, Vehicle.policy_id == policy_id)
        )
        return result.scalar_one_or_none() is not None
