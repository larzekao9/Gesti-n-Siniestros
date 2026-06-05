"""Claim request domain service — CU-24, CU-25, and supporting operations."""

from datetime import date, datetime, time, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim_request import ClaimRequest, ClaimRequestStatus
from app.models.evidence import Evidence
from app.models.notification import NotificationKind
from app.models.state_transition import StateTransition, SubjectType
from app.models.user import Role, User
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
from app.services.notification_service import notification_service
from app.services.workflow_service import WorkflowService

audit_service = AuditService()
workflow_service = WorkflowService()


class ClaimRequestService:
    """Manages claim request lifecycle: draft → submitted → under_intake_review → formalized/rejected."""

    async def create_draft(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        policyholder_id: UUID,
        policy_id: UUID,
        vehicle_id: UUID,
        accident_date: date | None = None,
        accident_time: time | None = None,
        accident_location: str | None = None,
        accident_lat: Decimal | None = None,
        accident_lng: Decimal | None = None,
        accident_description: str | None = None,
        reported_damages: str | None = None,
        actor_user_id: UUID | None = None,
        created_by_account_id: UUID | None = None,
    ) -> ClaimRequest:
        # Validate catalog entities exist in tenant
        ph = await db.execute(
            select(Policyholder).where(
                Policyholder.id == policyholder_id, Policyholder.tenant_id == tenant_id
            )
        )
        if ph.scalar_one_or_none() is None:
            raise NotFoundError("Asegurado no encontrado")

        pol = await db.execute(
            select(Policy).where(
                Policy.id == policy_id, Policy.tenant_id == tenant_id
            )
        )
        if pol.scalar_one_or_none() is None:
            raise NotFoundError("Póliza no encontrada")

        veh = await db.execute(
            select(Vehicle).where(
                Vehicle.id == vehicle_id, Vehicle.tenant_id == tenant_id
            )
        )
        if veh.scalar_one_or_none() is None:
            raise NotFoundError("Vehículo no encontrado")

        cr = ClaimRequest(
            tenant_id=tenant_id,
            status=ClaimRequestStatus.DRAFT,
            created_by_account_id=created_by_account_id,
            policyholder_id=policyholder_id,
            policy_id=policy_id,
            vehicle_id=vehicle_id,
            accident_date=accident_date,
            accident_time=accident_time,
            accident_location=accident_location,
            accident_lat=accident_lat,
            accident_lng=accident_lng,
            accident_description=accident_description,
            reported_damages=reported_damages,
        )
        db.add(cr)
        await db.flush()

        await audit_service.write(
            db,
            tenant_id=tenant_id,
            action="CREATE_DRAFT",
            entity_type="claim_request",
            entity_id=cr.id,
            actor_user_id=actor_user_id,
            actor_account_id=created_by_account_id,
        )
        await db.refresh(cr)
        return cr

    # ── Canal asegurado (CU-02/03/05/06) ───────────────────────────

    async def get_for_account(
        self, db: AsyncSession, *, request_id: UUID, tenant_id: UUID, account_id: UUID
    ) -> ClaimRequest:
        """Carga una solicitud verificando que pertenezca a la cuenta del asegurado.

        Cross-account devuelve 404 (no 403) para no filtrar existencia.
        """
        result = await db.execute(
            select(ClaimRequest).where(
                ClaimRequest.id == request_id,
                ClaimRequest.tenant_id == tenant_id,
                ClaimRequest.created_by_account_id == account_id,
            )
        )
        cr = result.scalar_one_or_none()
        if cr is None:
            raise NotFoundError("Solicitud no encontrada")
        return cr

    async def list_for_account(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        account_id: UUID,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[ClaimRequest], int]:
        offset = (page - 1) * limit
        query = select(ClaimRequest).where(
            ClaimRequest.tenant_id == tenant_id,
            ClaimRequest.created_by_account_id == account_id,
        )
        count_q = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_q)).scalar_one()

        query = query.order_by(ClaimRequest.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all()), total

    async def update_draft(
        self,
        db: AsyncSession,
        *,
        request_id: UUID,
        tenant_id: UUID,
        account_id: UUID,
        fields: dict,
    ) -> ClaimRequest:
        """Auto-guardado de un paso del wizard. Solo permitido en estado draft."""
        cr = await self.get_for_account(
            db, request_id=request_id, tenant_id=tenant_id, account_id=account_id
        )
        if cr.status != ClaimRequestStatus.DRAFT:
            raise ConflictError("Solo se puede editar una solicitud en borrador")

        # Validar entidades del catálogo si se cambian.
        if fields.get("policyholder_id") is not None:
            ph = await db.execute(
                select(Policyholder).where(
                    Policyholder.id == fields["policyholder_id"],
                    Policyholder.tenant_id == tenant_id,
                )
            )
            if ph.scalar_one_or_none() is None:
                raise NotFoundError("Asegurado no encontrado")
        if fields.get("policy_id") is not None:
            pol = await db.execute(
                select(Policy).where(
                    Policy.id == fields["policy_id"], Policy.tenant_id == tenant_id
                )
            )
            if pol.scalar_one_or_none() is None:
                raise NotFoundError("Póliza no encontrada")
        if fields.get("vehicle_id") is not None:
            veh = await db.execute(
                select(Vehicle).where(
                    Vehicle.id == fields["vehicle_id"], Vehicle.tenant_id == tenant_id
                )
            )
            if veh.scalar_one_or_none() is None:
                raise NotFoundError("Vehículo no encontrado")

        editable = {
            "policyholder_id", "policy_id", "vehicle_id", "accident_date",
            "accident_time", "accident_location", "accident_lat", "accident_lng",
            "accident_description", "reported_damages",
        }
        for key, value in fields.items():
            if key in editable and value is not None:
                setattr(cr, key, value)

        await db.flush()
        await audit_service.write(
            db,
            tenant_id=tenant_id,
            action="UPDATE_DRAFT",
            entity_type="claim_request",
            entity_id=cr.id,
            actor_account_id=account_id,
        )
        await db.refresh(cr)
        return cr

    async def delete_draft(
        self, db: AsyncSession, *, request_id: UUID, tenant_id: UUID, account_id: UUID
    ) -> None:
        """Descarta un borrador. Solo permitido en estado draft (CU-02 F-A2)."""
        cr = await self.get_for_account(
            db, request_id=request_id, tenant_id=tenant_id, account_id=account_id
        )
        if cr.status != ClaimRequestStatus.DRAFT:
            raise ConflictError("Solo se puede descartar una solicitud en borrador")

        await audit_service.write(
            db,
            tenant_id=tenant_id,
            action="DELETE_DRAFT",
            entity_type="claim_request",
            entity_id=cr.id,
            actor_account_id=account_id,
        )
        await db.delete(cr)
        await db.flush()

    async def _validate_minimal_data(
        self, db: AsyncSession, cr: ClaimRequest
    ) -> None:
        """Valida completitud mínima para enviar (CU-05). 422 con campos faltantes."""
        missing: list[str] = []
        if cr.vehicle_id is None:
            missing.append("vehicle_id")
        if cr.policy_id is None:
            missing.append("policy_id")
        if cr.accident_date is None:
            missing.append("accident_date")
        if not cr.accident_location:
            missing.append("accident_location")
        if not cr.accident_description:
            missing.append("accident_description")

        # Al menos una evidencia inicial cargada (CU-04).
        ev_count = await db.execute(
            select(func.count()).select_from(
                select(Evidence).where(
                    Evidence.claim_request_id == cr.id,
                    Evidence.tenant_id == cr.tenant_id,
                ).subquery()
            )
        )
        if ev_count.scalar_one() == 0:
            missing.append("evidences")

        if missing:
            raise ValidationError(
                "Solicitud incompleta. Faltan campos: " + ", ".join(missing)
            )

    async def submit(
        self, db: AsyncSession, *, request_id: UUID, tenant_id: UUID, account_id: UUID
    ) -> ClaimRequest:
        """Envía el borrador: draft → submitted (CU-05). Transacción atómica."""
        cr = await self.get_for_account(
            db, request_id=request_id, tenant_id=tenant_id, account_id=account_id
        )

        if cr.status != ClaimRequestStatus.DRAFT:
            raise ConflictError("La solicitud ya fue enviada")

        # Valida la transición vía la state machine + completitud mínima.
        workflow_service.validate_transition(
            current=cr.status, target=ClaimRequestStatus.SUBMITTED
        )
        await self._validate_minimal_data(db, cr)

        old_status = cr.status
        cr.status = ClaimRequestStatus.SUBMITTED
        cr.request_number = await self._generate_request_number(db, tenant_id=tenant_id)
        cr.submitted_at = datetime.now(timezone.utc).replace(tzinfo=None)

        transition = StateTransition(
            tenant_id=tenant_id,
            subject_type=SubjectType.CLAIM_REQUEST,
            subject_id=cr.id,
            from_status=old_status.value,
            to_status=cr.status.value,
            actor_account_id=account_id,
        )
        db.add(transition)
        await db.flush()

        # Notificar a los analistas del tenant (entran a la bandeja de intake).
        analysts = await db.execute(
            select(User).where(
                User.tenant_id == tenant_id,
                User.role == Role.ANALYST,
                User.is_active == True,  # noqa: E712
            )
        )
        for analyst in analysts.scalars().all():
            await notification_service.create(
                db,
                tenant_id=tenant_id,
                recipient_user_id=analyst.id,
                entity_type="claim_request",
                entity_id=cr.id,
                kind=NotificationKind.CLAIM_CREATED,
                title="Nueva solicitud de siniestro",
                body=f"Solicitud {cr.request_number} pendiente de revisión",
            )

        await audit_service.write(
            db,
            tenant_id=tenant_id,
            action="SUBMIT_CLAIM_REQUEST",
            entity_type="claim_request",
            entity_id=cr.id,
            actor_account_id=account_id,
            payload_diff={"request_number": cr.request_number},
        )
        await db.refresh(cr)
        return cr

    async def get_request(
        self, db: AsyncSession, *, request_id: UUID, tenant_id: UUID
    ) -> ClaimRequest:
        result = await db.execute(
            select(ClaimRequest).where(
                ClaimRequest.id == request_id, ClaimRequest.tenant_id == tenant_id
            )
        )
        cr = result.scalar_one_or_none()
        if cr is None:
            raise NotFoundError("Solicitud no encontrada")
        return cr

    async def take(
        self,
        db: AsyncSession,
        *,
        request_id: UUID,
        tenant_id: UUID,
        actor_user_id: UUID,
    ) -> ClaimRequest:
        # Row-level lock to serialize concurrent take attempts (CU-24).
        # On PostgreSQL this emits SELECT ... FOR UPDATE; on SQLite (tests) it's a no-op
        # but the application-level status check still preserves correctness.
        result = await db.execute(
            select(ClaimRequest)
            .where(
                ClaimRequest.id == request_id,
                ClaimRequest.tenant_id == tenant_id,
            )
            .with_for_update()
        )
        cr = result.scalar_one_or_none()
        if cr is None:
            raise NotFoundError("Solicitud no encontrada")

        if cr.status != ClaimRequestStatus.SUBMITTED:
            raise ConflictError(
                f"La solicitud ya fue tomada por otro analista (estado actual: {cr.status.value})"
            )

        old_status = cr.status
        cr.status = ClaimRequestStatus.UNDER_INTAKE_REVIEW
        cr.reviewed_by_user_id = actor_user_id

        transition = StateTransition(
            tenant_id=tenant_id,
            subject_type=SubjectType.CLAIM_REQUEST,
            subject_id=cr.id,
            from_status=old_status.value,
            to_status=cr.status.value,
            actor_user_id=actor_user_id,
        )
        db.add(transition)
        await db.flush()

        await audit_service.write(
            db,
            tenant_id=tenant_id,
            action="TAKE_REQUEST",
            entity_type="claim_request",
            entity_id=cr.id,
            actor_user_id=actor_user_id,
        )
        await db.refresh(cr)
        return cr

    async def release(
        self,
        db: AsyncSession,
        *,
        request_id: UUID,
        tenant_id: UUID,
        actor_user_id: UUID,
    ) -> ClaimRequest:
        cr = await self.get_request(db, request_id=request_id, tenant_id=tenant_id)

        if cr.status != ClaimRequestStatus.UNDER_INTAKE_REVIEW:
            raise ConflictError("La solicitud no está en revisión de intake")

        if cr.reviewed_by_user_id != actor_user_id:
            raise PermissionError("Solo el analista que tomó la solicitud puede liberarla")

        old_status = cr.status
        cr.status = ClaimRequestStatus.SUBMITTED
        cr.reviewed_by_user_id = None

        transition = StateTransition(
            tenant_id=tenant_id,
            subject_type=SubjectType.CLAIM_REQUEST,
            subject_id=cr.id,
            from_status=old_status.value,
            to_status=cr.status.value,
            actor_user_id=actor_user_id,
        )
        db.add(transition)
        await db.flush()

        await audit_service.write(
            db,
            tenant_id=tenant_id,
            action="RELEASE_REQUEST",
            entity_type="claim_request",
            entity_id=cr.id,
            actor_user_id=actor_user_id,
        )
        await db.refresh(cr)
        return cr

    async def reassign(
        self,
        db: AsyncSession,
        *,
        request_id: UUID,
        tenant_id: UUID,
        target_user_id: UUID,
        actor_user_id: UUID,
    ) -> ClaimRequest:
        cr = await self.get_request(db, request_id=request_id, tenant_id=tenant_id)

        if cr.status != ClaimRequestStatus.UNDER_INTAKE_REVIEW:
            raise ConflictError("La solicitud no está en revisión de intake")

        old_reviewer = cr.reviewed_by_user_id
        cr.reviewed_by_user_id = target_user_id

        await db.flush()

        await audit_service.write(
            db,
            tenant_id=tenant_id,
            action="REASSIGN_REQUEST",
            entity_type="claim_request",
            entity_id=cr.id,
            actor_user_id=actor_user_id,
            payload_diff={"previous_reviewer": str(old_reviewer), "new_reviewer": str(target_user_id)},
        )
        return cr

    async def reject_at_intake(
        self,
        db: AsyncSession,
        *,
        request_id: UUID,
        tenant_id: UUID,
        reason: str,
        actor_user_id: UUID,
    ) -> ClaimRequest:
        cr = await self.get_request(db, request_id=request_id, tenant_id=tenant_id)

        if cr.status != ClaimRequestStatus.UNDER_INTAKE_REVIEW:
            raise ConflictError("La solicitud debe estar en revisión de intake para ser rechazada")

        if cr.reviewed_by_user_id != actor_user_id:
            raise PermissionError("Solo el analista que tomó la solicitud puede rechazarla")

        old_status = cr.status
        cr.status = ClaimRequestStatus.REJECTED_AT_INTAKE
        cr.intake_decision_reason = reason

        transition = StateTransition(
            tenant_id=tenant_id,
            subject_type=SubjectType.CLAIM_REQUEST,
            subject_id=cr.id,
            from_status=old_status.value,
            to_status=cr.status.value,
            reason=reason,
            actor_user_id=actor_user_id,
        )
        db.add(transition)
        await db.flush()

        # Retro-enganche Ciclo 7: notificar al asegurado del rechazo en intake (CU-25).
        # Si la solicitud no vino del canal móvil (sin cuenta), create() es no-op.
        if cr.created_by_account_id is not None:
            await notification_service.create(
                db,
                tenant_id=tenant_id,
                recipient_account_id=cr.created_by_account_id,
                entity_type="claim_request",
                entity_id=cr.id,
                kind=NotificationKind.INTAKE_REJECTED,
                title="Solicitud rechazada",
                body=f"Tu solicitud {cr.request_number or ''} fue rechazada. Motivo: {reason}",
            )

        await audit_service.write(
            db,
            tenant_id=tenant_id,
            action="REJECT_AT_INTAKE",
            entity_type="claim_request",
            entity_id=cr.id,
            actor_user_id=actor_user_id,
            payload_diff={"reason": reason},
        )
        await db.refresh(cr)
        return cr

    async def _generate_request_number(
        self, db: AsyncSession, *, tenant_id: UUID
    ) -> str:
        year = str(datetime.now(timezone.utc).year)
        prefix = f"REQ-{year}-"
        result = await db.execute(
            select(func.max(ClaimRequest.request_number)).where(
                ClaimRequest.tenant_id == tenant_id,
                ClaimRequest.request_number.like(f"{prefix}%"),
            )
        )
        max_num = result.scalar_one_or_none()
        if max_num:
            seq = int(max_num[len(prefix) :]) + 1
        else:
            seq = 1
        return f"{prefix}{seq:06d}"

    async def search(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        q: str | None = None,
        status: str | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[ClaimRequest], int]:
        offset = (page - 1) * limit
        query = select(ClaimRequest).where(ClaimRequest.tenant_id == tenant_id)

        if status:
            query = query.where(ClaimRequest.status == status)
        if from_date:
            query = query.where(ClaimRequest.accident_date >= from_date)
        if to_date:
            query = query.where(ClaimRequest.accident_date <= to_date)
        if q:
            pattern = f"%{q}%"
            query = query.where(
                (ClaimRequest.request_number.ilike(pattern))
                | (ClaimRequest.accident_location.ilike(pattern))
                | (ClaimRequest.accident_description.ilike(pattern))
            )

        count_q = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_q)).scalar_one()

        query = query.order_by(ClaimRequest.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all()), total
