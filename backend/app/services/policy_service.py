"""Policy domain service."""

from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.policy import Policy
from app.models.policyholder import Policyholder
from app.services.audit_service import AuditService
from app.services.exceptions import ConflictError, NotFoundError, ValidationError

audit_service = AuditService()


class PolicyService:
    """CRUD for insurance policies."""

    async def list_policies(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        page: int = 1,
        limit: int = 20,
        policyholder_id: UUID | None = None,
        search: str | None = None,
    ) -> tuple[list[Policy], int]:
        offset = (page - 1) * limit
        query = select(Policy).where(Policy.tenant_id == tenant_id)

        if policyholder_id:
            query = query.where(Policy.policyholder_id == policyholder_id)
        if search:
            pattern = f"%{search}%"
            query = query.where(
                (Policy.policy_number.ilike(pattern)) | (Policy.coverage_type.ilike(pattern))
            )

        count_q = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_q)).scalar_one()

        query = query.order_by(Policy.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all()), total

    async def get_policy(
        self, db: AsyncSession, *, policy_id: UUID, tenant_id: UUID
    ) -> Policy:
        result = await db.execute(
            select(Policy).where(Policy.id == policy_id, Policy.tenant_id == tenant_id)
        )
        policy = result.scalar_one_or_none()
        if policy is None:
            raise NotFoundError("Póliza no encontrada")
        return policy

    async def create_policy(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        policy_number: str,
        policyholder_id: UUID,
        valid_from: date,
        valid_to: date,
        coverage_type: str,
        exclusions: str | None = None,
        actor_user_id: UUID,
    ) -> Policy:
        if valid_from >= valid_to:
            raise ValidationError("La fecha de inicio debe ser anterior a la de fin")

        ph_result = await db.execute(
            select(Policyholder).where(
                Policyholder.id == policyholder_id, Policyholder.tenant_id == tenant_id
            )
        )
        if ph_result.scalar_one_or_none() is None:
            raise NotFoundError("Asegurado no encontrado")

        existing = await db.execute(
            select(Policy).where(
                Policy.tenant_id == tenant_id, Policy.policy_number == policy_number
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise ConflictError("Ya existe una póliza con ese número en este tenant")

        policy = Policy(
            tenant_id=tenant_id,
            policy_number=policy_number,
            policyholder_id=policyholder_id,
            valid_from=valid_from,
            valid_to=valid_to,
            coverage_type=coverage_type,
            exclusions=exclusions,
        )
        db.add(policy)
        await db.flush()

        await audit_service.write(
            db,
            tenant_id=tenant_id,
            action="CREATE_POLICY",
            entity_type="policy",
            entity_id=policy.id,
            actor_user_id=actor_user_id,
            payload_diff={"policy_number": policy_number, "policyholder_id": str(policyholder_id)},
        )
        return policy

    async def update_policy(
        self,
        db: AsyncSession,
        *,
        policy_id: UUID,
        tenant_id: UUID,
        policy_number: str | None = None,
        valid_from: date | None = None,
        valid_to: date | None = None,
        coverage_type: str | None = None,
        exclusions: str | None = None,
        status: str | None = None,
        actor_user_id: UUID,
    ) -> Policy:
        policy = await self.get_policy(db, policy_id=policy_id, tenant_id=tenant_id)
        changes: dict = {}

        if policy_number is not None and policy_number != policy.policy_number:
            existing = await db.execute(
                select(Policy).where(
                    Policy.tenant_id == tenant_id, Policy.policy_number == policy_number
                )
            )
            if existing.scalar_one_or_none() is not None:
                raise ConflictError("Ya existe una póliza con ese número en este tenant")
            policy.policy_number = policy_number
            changes["policy_number"] = policy_number

        new_from = valid_from if valid_from is not None else policy.valid_from
        new_to = valid_to if valid_to is not None else policy.valid_to
        if new_from >= new_to:
            raise ValidationError("La fecha de inicio debe ser anterior a la de fin")

        if valid_from is not None:
            policy.valid_from = valid_from
            changes["valid_from"] = valid_from.isoformat()
        if valid_to is not None:
            policy.valid_to = valid_to
            changes["valid_to"] = valid_to.isoformat()
        if coverage_type is not None:
            policy.coverage_type = coverage_type
            changes["coverage_type"] = coverage_type
        if exclusions is not None:
            policy.exclusions = exclusions
            changes["exclusions"] = exclusions
        if status is not None:
            policy.status = status
            changes["status"] = status

        await db.flush()
        await db.refresh(policy)

        await audit_service.write(
            db,
            tenant_id=tenant_id,
            action="UPDATE_POLICY",
            entity_type="policy",
            entity_id=policy.id,
            actor_user_id=actor_user_id,
            payload_diff=changes or None,
        )
        return policy

    async def is_valid_at(self, db: AsyncSession, *, policy_id: UUID, at_date: date) -> bool:
        policy = await db.execute(
            select(Policy).where(Policy.id == policy_id)
        )
        policy = policy.scalar_one_or_none()
        if policy is None:
            return False
        return policy.valid_from <= at_date <= policy.valid_to and policy.status == "active"
