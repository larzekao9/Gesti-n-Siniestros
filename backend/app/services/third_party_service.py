"""Third party domain service — CU-17."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim import Claim
from app.models.third_party import ThirdParty, ThirdPartyKind
from app.services.audit_service import AuditService
from app.services.exceptions import NotFoundError, ValidationError

audit_service = AuditService()


class ThirdPartyService:
    """CRUD for third parties involved in a claim."""

    async def create(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        claim_id: UUID,
        kind: str,
        full_name: str,
        document_id: str | None = None,
        contact_phone: str | None = None,
        vehicle_plate: str | None = None,
        vehicle_info: str | None = None,
        statement: str | None = None,
        actor_user_id: UUID,
    ) -> ThirdParty:
        # Validate claim exists
        result = await db.execute(
            select(Claim).where(Claim.id == claim_id, Claim.tenant_id == tenant_id)
        )
        if result.scalar_one_or_none() is None:
            raise NotFoundError("Expediente no encontrado")

        # Validate kind
        try:
            tp_kind = ThirdPartyKind(kind)
        except ValueError:
            raise ValidationError(
                f"Tipo de tercero inválido: {kind}. Válidos: {[k.value for k in ThirdPartyKind]}"
            )

        tp = ThirdParty(
            tenant_id=tenant_id,
            claim_id=claim_id,
            kind=tp_kind,
            full_name=full_name,
            document_id=document_id,
            contact_phone=contact_phone,
            vehicle_plate=vehicle_plate,
            vehicle_info=vehicle_info,
            statement=statement,
        )
        db.add(tp)
        await db.flush()

        await audit_service.write(
            db,
            tenant_id=tenant_id,
            action="CREATE_THIRD_PARTY",
            entity_type="third_party",
            entity_id=tp.id,
            actor_user_id=actor_user_id,
            payload_diff={"kind": kind, "full_name": full_name},
        )
        await db.refresh(tp)
        return tp

    async def update(
        self,
        db: AsyncSession,
        *,
        third_party_id: UUID,
        tenant_id: UUID,
        kind: str | None = None,
        full_name: str | None = None,
        document_id: str | None = None,
        contact_phone: str | None = None,
        vehicle_plate: str | None = None,
        vehicle_info: str | None = None,
        statement: str | None = None,
        actor_user_id: UUID,
    ) -> ThirdParty:
        result = await db.execute(
            select(ThirdParty).where(
                ThirdParty.id == third_party_id, ThirdParty.tenant_id == tenant_id
            )
        )
        tp = result.scalar_one_or_none()
        if tp is None:
            raise NotFoundError("Tercero no encontrado")

        if kind is not None:
            try:
                tp.kind = ThirdPartyKind(kind)
            except ValueError:
                raise ValidationError(
                    f"Tipo de tercero inválido: {kind}"
                )
        if full_name is not None:
            tp.full_name = full_name
        if document_id is not None:
            tp.document_id = document_id
        if contact_phone is not None:
            tp.contact_phone = contact_phone
        if vehicle_plate is not None:
            tp.vehicle_plate = vehicle_plate
        if vehicle_info is not None:
            tp.vehicle_info = vehicle_info
        if statement is not None:
            tp.statement = statement

        await db.flush()
        await db.refresh(tp)

        await audit_service.write(
            db,
            tenant_id=tenant_id,
            action="UPDATE_THIRD_PARTY",
            entity_type="third_party",
            entity_id=tp.id,
            actor_user_id=actor_user_id,
        )
        return tp

    async def delete(
        self,
        db: AsyncSession,
        *,
        third_party_id: UUID,
        tenant_id: UUID,
        actor_user_id: UUID,
    ) -> None:
        tp = await db.execute(
            select(ThirdParty).where(
                ThirdParty.id == third_party_id, ThirdParty.tenant_id == tenant_id
            )
        )
        tp = tp.scalar_one_or_none()
        if tp is None:
            raise NotFoundError("Tercero no encontrado")

        await db.delete(tp)

        await audit_service.write(
            db,
            tenant_id=tenant_id,
            action="DELETE_THIRD_PARTY",
            entity_type="third_party",
            entity_id=third_party_id,
            actor_user_id=actor_user_id,
        )

    async def list_for_claim(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        claim_id: UUID,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[ThirdParty], int]:
        offset = (page - 1) * limit
        query = select(ThirdParty).where(
            ThirdParty.tenant_id == tenant_id, ThirdParty.claim_id == claim_id
        )

        count_q = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_q)).scalar_one()

        query = query.order_by(ThirdParty.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all()), total
