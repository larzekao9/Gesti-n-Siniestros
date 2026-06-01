"""Observation domain service — CU-14."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim import Claim, ClaimStatus
from app.models.observation import Observation
from app.services.audit_service import AuditService
from app.services.exceptions import ConflictError, NotFoundError, ValidationError

audit_service = AuditService()


class ObservationService:
    """CRUD for observations on a claim."""

    async def create(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        claim_id: UUID,
        comment: str,
        is_internal: bool = False,
        actor_user_id: UUID,
    ) -> Observation:
        # Validate claim exists and is not closed
        result = await db.execute(
            select(Claim).where(Claim.id == claim_id, Claim.tenant_id == tenant_id)
        )
        claim = result.scalar_one_or_none()
        if claim is None:
            raise NotFoundError("Expediente no encontrado")
        if claim.status == ClaimStatus.CLOSED:
            raise ConflictError("No se pueden agregar observaciones a un expediente cerrado")

        obs = Observation(
            tenant_id=tenant_id,
            claim_id=claim_id,
            author_user_id=actor_user_id,
            comment=comment,
            is_internal=is_internal,
        )
        db.add(obs)
        await db.flush()

        await audit_service.write(
            db,
            tenant_id=tenant_id,
            action="CREATE_OBSERVATION",
            entity_type="observation",
            entity_id=obs.id,
            actor_user_id=actor_user_id,
            payload_diff={"is_internal": is_internal},
        )
        await db.refresh(obs)
        return obs

    async def list_for_claim(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        claim_id: UUID,
        page: int = 1,
        limit: int = 20,
        include_internal: bool = True,
    ) -> tuple[list[Observation], int]:
        offset = (page - 1) * limit
        query = select(Observation).where(
            Observation.tenant_id == tenant_id, Observation.claim_id == claim_id
        )
        if not include_internal:
            query = query.where(Observation.is_internal.is_(False))

        count_q = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_q)).scalar_one()

        query = query.order_by(Observation.created_at.asc()).offset(offset).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all()), total
