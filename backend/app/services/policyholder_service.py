"""Policyholder domain service."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.policyholder import Policyholder
from app.services.audit_service import AuditService
from app.services.exceptions import ConflictError, NotFoundError

audit_service = AuditService()


class PolicyholderService:
    """CRUD for insured persons."""

    async def list_policyholders(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        page: int = 1,
        limit: int = 20,
        search: str | None = None,
    ) -> tuple[list[Policyholder], int]:
        offset = (page - 1) * limit
        query = select(Policyholder).where(Policyholder.tenant_id == tenant_id)

        if search:
            pattern = f"%{search}%"
            query = query.where(
                (Policyholder.full_name.ilike(pattern)) | (Policyholder.document_id.ilike(pattern))
            )

        count_q = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_q)).scalar_one()

        query = query.order_by(Policyholder.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all()), total

    async def get_policyholder(
        self, db: AsyncSession, *, policyholder_id: UUID, tenant_id: UUID
    ) -> Policyholder:
        result = await db.execute(
            select(Policyholder).where(
                Policyholder.id == policyholder_id, Policyholder.tenant_id == tenant_id
            )
        )
        ph = result.scalar_one_or_none()
        if ph is None:
            raise NotFoundError("Asegurado no encontrado")
        return ph

    async def create_policyholder(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        document_id: str,
        full_name: str,
        phone: str,
        email: str | None = None,
        address: str | None = None,
        actor_user_id: UUID,
    ) -> Policyholder:
        existing = await db.execute(
            select(Policyholder).where(
                Policyholder.tenant_id == tenant_id,
                Policyholder.document_id == document_id,
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise ConflictError("Ya existe un asegurado con ese documento en este tenant")

        ph = Policyholder(
            tenant_id=tenant_id,
            document_id=document_id,
            full_name=full_name,
            phone=phone,
            email=email,
            address=address,
        )
        db.add(ph)
        await db.flush()

        await audit_service.write(
            db,
            tenant_id=tenant_id,
            action="CREATE_POLICYHOLDER",
            entity_type="policyholder",
            entity_id=ph.id,
            actor_user_id=actor_user_id,
            payload_diff={"document_id": document_id, "full_name": full_name},
        )
        return ph

    async def update_policyholder(
        self,
        db: AsyncSession,
        *,
        policyholder_id: UUID,
        tenant_id: UUID,
        full_name: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        address: str | None = None,
        status: str | None = None,
        actor_user_id: UUID,
    ) -> Policyholder:
        ph = await self.get_policyholder(db, policyholder_id=policyholder_id, tenant_id=tenant_id)
        changes: dict = {}
        if full_name is not None:
            ph.full_name = full_name
            changes["full_name"] = full_name
        if phone is not None:
            ph.phone = phone
            changes["phone"] = phone
        if email is not None:
            ph.email = email
            changes["email"] = email
        if address is not None:
            ph.address = address
            changes["address"] = address
        if status is not None:
            ph.status = status
            changes["status"] = status
        await db.flush()
        await db.refresh(ph)

        await audit_service.write(
            db,
            tenant_id=tenant_id,
            action="UPDATE_POLICYHOLDER",
            entity_type="policyholder",
            entity_id=ph.id,
            actor_user_id=actor_user_id,
            payload_diff=changes or None,
        )
        return ph
