"""Claim domain service — CU-10 formalization and lifecycle."""

from datetime import date, datetime, time, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim import Claim, ClaimSource, ClaimStatus, ClaimDecision
from app.models.claim_request import ClaimRequest, ClaimRequestStatus
from app.models.state_transition import StateTransition, SubjectType
from app.models.policyholder import Policyholder
from app.models.policy import Policy
from app.models.vehicle import Vehicle
from app.services.audit_service import AuditService
from app.services.exceptions import (
    ConflictError,
    NotFoundError,
    PermissionError,
    ValidationError,
)
from app.services.policy_service import PolicyService
from app.services.vehicle_service import VehicleService

audit_service = AuditService()
policy_service = PolicyService()
vehicle_service = VehicleService()


class ClaimService:
    """Manages claim (expediente) lifecycle."""

    async def get_claim(
        self, db: AsyncSession, *, claim_id: UUID, tenant_id: UUID
    ) -> Claim:
        result = await db.execute(
            select(Claim).where(Claim.id == claim_id, Claim.tenant_id == tenant_id)
        )
        claim = result.scalar_one_or_none()
        if claim is None:
            raise NotFoundError("Expediente no encontrado")
        return claim

    async def get_claim_with_related(
        self, db: AsyncSession, *, claim_id: UUID, tenant_id: UUID
    ) -> tuple[Claim, Policyholder | None, Policy | None, Vehicle | None]:
        claim = await self.get_claim(db, claim_id=claim_id, tenant_id=tenant_id)
        ph = (await db.execute(
            select(Policyholder).where(
                Policyholder.id == claim.policyholder_id,
                Policyholder.tenant_id == tenant_id,
            )
        )).scalar_one_or_none()
        pol = (await db.execute(
            select(Policy).where(
                Policy.id == claim.policy_id, Policy.tenant_id == tenant_id
            )
        )).scalar_one_or_none()
        veh = (await db.execute(
            select(Vehicle).where(
                Vehicle.id == claim.vehicle_id, Vehicle.tenant_id == tenant_id
            )
        )).scalar_one_or_none()
        return claim, ph, pol, veh

    async def get_by_number(
        self, db: AsyncSession, *, claim_number: str, tenant_id: UUID
    ) -> Claim | None:
        result = await db.execute(
            select(Claim).where(
                Claim.claim_number == claim_number, Claim.tenant_id == tenant_id
            )
        )
        return result.scalar_one_or_none()

    async def _generate_claim_number(
        self, db: AsyncSession, *, tenant_id: UUID
    ) -> str:
        year = str(datetime.now(timezone.utc).year)
        prefix = f"EXP-{year}-"
        result = await db.execute(
            select(func.max(Claim.claim_number)).where(
                Claim.tenant_id == tenant_id,
                Claim.claim_number.like(f"{prefix}%"),
            )
        )
        max_num = result.scalar_one_or_none()
        if max_num:
            seq = int(max_num[len(prefix) :]) + 1
        else:
            seq = 1
        return f"{prefix}{seq:06d}"

    async def create_internal(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        policyholder_id: UUID,
        policy_id: UUID,
        vehicle_id: UUID,
        accident_date: date,
        accident_time: time | None = None,
        accident_location: str = "",
        accident_lat: Decimal | None = None,
        accident_lng: Decimal | None = None,
        accident_description: str | None = None,
        reported_damages: str | None = None,
        actor_user_id: UUID,
    ) -> Claim:
        # Validate catalog entities
        ph = await db.execute(
            select(Policyholder).where(
                Policyholder.id == policyholder_id, Policyholder.tenant_id == tenant_id
            )
        )
        if ph.scalar_one_or_none() is None:
            raise NotFoundError("Asegurado no encontrado")

        pol = await db.execute(
            select(Policy).where(Policy.id == policy_id, Policy.tenant_id == tenant_id)
        )
        if pol.scalar_one_or_none() is None:
            raise NotFoundError("Póliza no encontrada")

        # Validate policy is valid at accident date
        if not await policy_service.is_valid_at(db, policy_id=policy_id, at_date=accident_date):
            raise ValidationError(
                "La póliza no está vigente en la fecha del accidente",
            )

        # Validate vehicle belongs to policy
        if not await vehicle_service.belongs_to_policy(
            db, vehicle_id=vehicle_id, policy_id=policy_id
        ):
            raise ValidationError(
                "El vehículo no pertenece a la póliza seleccionada",
            )

        claim_number = await self._generate_claim_number(db, tenant_id=tenant_id)

        claim = Claim(
            tenant_id=tenant_id,
            claim_number=claim_number,
            policyholder_id=policyholder_id,
            policy_id=policy_id,
            vehicle_id=vehicle_id,
            status=ClaimStatus.REGISTERED,
            source=ClaimSource.INTERNAL,
            accident_date=accident_date,
            accident_time=accident_time,
            accident_location=accident_location,
            accident_lat=accident_lat,
            accident_lng=accident_lng,
            accident_description=accident_description,
            reported_damages=reported_damages,
            created_by_user_id=actor_user_id,
            assigned_analyst_id=actor_user_id,
        )
        db.add(claim)
        await db.flush()

        # Write initial state transition
        transition = StateTransition(
            tenant_id=tenant_id,
            subject_type=SubjectType.CLAIM,
            subject_id=claim.id,
            from_status=None,
            to_status=ClaimStatus.REGISTERED.value,
            actor_user_id=actor_user_id,
        )
        db.add(transition)

        await audit_service.write(
            db,
            tenant_id=tenant_id,
            action="CREATE_CLAIM",
            entity_type="claim",
            entity_id=claim.id,
            actor_user_id=actor_user_id,
            payload_diff={"source": "internal", "claim_number": claim_number},
        )
        await db.refresh(claim)
        return claim

    async def formalize_request(
        self,
        db: AsyncSession,
        *,
        request_id: UUID,
        tenant_id: UUID,
        actor_user_id: UUID,
    ) -> tuple[Claim, ClaimRequest]:
        """Formalize a claim request into a full claim (CU-10).

        Executed in a single transaction by the caller.
        """
        cr = await db.execute(
            select(ClaimRequest).where(
                ClaimRequest.id == request_id, ClaimRequest.tenant_id == tenant_id
            )
        )
        cr = cr.scalar_one_or_none()
        if cr is None:
            raise NotFoundError("Solicitud no encontrada")

        # Validate request state
        if cr.status not in (
            ClaimRequestStatus.SUBMITTED,
            ClaimRequestStatus.UNDER_INTAKE_REVIEW,
        ):
            raise ConflictError(
                f"La solicitud no puede formalizarse (estado: {cr.status.value})"
            )

        if cr.formalized_claim_id is not None:
            raise ConflictError("La solicitud ya fue formalizada")

        # Validate accident_date is set
        if cr.accident_date is None:
            raise ValidationError("La solicitud no tiene fecha de accidente registrada")

        # Validate policy validity
        if not await policy_service.is_valid_at(
            db, policy_id=cr.policy_id, at_date=cr.accident_date
        ):
            raise ValidationError(
                "La póliza no está vigente en la fecha del accidente",
            )

        # Validate vehicle belongs to policy
        if not await vehicle_service.belongs_to_policy(
            db, vehicle_id=cr.vehicle_id, policy_id=cr.policy_id
        ):
            raise ValidationError(
                "El vehículo no pertenece a la póliza seleccionada",
            )

        # Generate claim number
        claim_number = await self._generate_claim_number(db, tenant_id=tenant_id)

        # Create the claim (snapshot from request)
        claim = Claim(
            tenant_id=tenant_id,
            claim_number=claim_number,
            claim_request_id=cr.id,
            policyholder_id=cr.policyholder_id,
            policy_id=cr.policy_id,
            vehicle_id=cr.vehicle_id,
            status=ClaimStatus.REGISTERED,
            source=ClaimSource.MOBILE_APP,
            accident_date=cr.accident_date,
            accident_time=cr.accident_time,
            accident_location=cr.accident_location or "",
            accident_lat=cr.accident_lat,
            accident_lng=cr.accident_lng,
            accident_description=cr.accident_description,
            reported_damages=cr.reported_damages,
            created_by_user_id=actor_user_id,
            assigned_analyst_id=actor_user_id,
        )
        db.add(claim)
        await db.flush()

        # Update the request
        old_request_status = cr.status
        cr.status = ClaimRequestStatus.FORMALIZED
        cr.formalized_claim_id = claim.id
        cr.reviewed_by_user_id = actor_user_id

        # Write state transitions for both entities
        req_transition = StateTransition(
            tenant_id=tenant_id,
            subject_type=SubjectType.CLAIM_REQUEST,
            subject_id=cr.id,
            from_status=old_request_status.value,
            to_status=cr.status.value,
            actor_user_id=actor_user_id,
        )
        db.add(req_transition)

        claim_transition = StateTransition(
            tenant_id=tenant_id,
            subject_type=SubjectType.CLAIM,
            subject_id=claim.id,
            from_status=None,
            to_status=ClaimStatus.REGISTERED.value,
            actor_user_id=actor_user_id,
        )
        db.add(claim_transition)

        await db.flush()

        # TODO Ciclo 4: promote evidences — add claim_id to evidences with claim_request_id=cr.id

        await audit_service.write(
            db,
            tenant_id=tenant_id,
            action="FORMALIZE",
            entity_type="claim",
            entity_id=claim.id,
            actor_user_id=actor_user_id,
            payload_diff={
                "request_id": str(cr.id),
                "request_number": cr.request_number,
                "claim_number": claim_number,
            },
        )
        await db.refresh(claim)
        await db.refresh(cr)
        return claim, cr

    async def update_status(
        self,
        db: AsyncSession,
        *,
        claim_id: UUID,
        tenant_id: UUID,
        new_status: str,
        reason: str | None,
        actor_user_id: UUID,
    ) -> Claim:
        claim = await self.get_claim(db, claim_id=claim_id, tenant_id=tenant_id)

        from app.models.claim import ClaimStatus as CS
        from app.services.workflow_service import WorkflowService

        wf = WorkflowService()
        current = CS(claim.status)
        target = CS(new_status)

        wf.validate_claim_transition(current=current, target=target)

        if wf.transitions_require_reason(current, target) and not reason:
            raise ValidationError("Se requiere motivo para esta transición")

        old_status = claim.status
        claim.status = target

        transition = StateTransition(
            tenant_id=tenant_id,
            subject_type=SubjectType.CLAIM,
            subject_id=claim.id,
            from_status=old_status.value,
            to_status=new_status,
            reason=reason,
            actor_user_id=actor_user_id,
        )
        db.add(transition)
        await db.flush()

        await audit_service.write(
            db,
            tenant_id=tenant_id,
            action="STATE_CHANGE",
            entity_type="claim",
            entity_id=claim.id,
            actor_user_id=actor_user_id,
            payload_diff={"from": old_status.value, "to": new_status, "reason": reason},
        )
        await db.refresh(claim)
        return claim

    async def search(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        q: str | None = None,
        status: str | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        analyst_id: str | None = None,
        policyholder_id: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Claim], int]:
        offset = (page - 1) * limit
        query = select(Claim).where(Claim.tenant_id == tenant_id)

        if status:
            query = query.where(Claim.status == status)
        if from_date:
            query = query.where(Claim.accident_date >= from_date)
        if to_date:
            query = query.where(Claim.accident_date <= to_date)
        if analyst_id:
            query = query.where(Claim.assigned_analyst_id == UUID(analyst_id))
        if policyholder_id:
            query = query.where(Claim.policyholder_id == UUID(policyholder_id))
        if q:
            pattern = f"%{q}%"
            query = query.where(
                (Claim.claim_number.ilike(pattern))
                | (Claim.accident_location.ilike(pattern))
                | (Claim.accident_description.ilike(pattern))
            )

        count_q = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_q)).scalar_one()

        query = query.order_by(Claim.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all()), total
