"""Audit log domain service — system-wide traceability."""

from __future__ import annotations

from datetime import date, datetime, time
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog

# Prefijos de acciones consideradas sensibles (CU-31 F-A2): visibles solo a
# admin, ocultas al supervisor y al analista. Forward-looking: cuando el
# AuthService registre LOGIN/PASSWORD_* en audit_logs, ya quedan filtradas.
_SENSITIVE_PREFIXES = ("LOGIN", "LOGOUT", "PASSWORD", "MFA")


class AuditService:
    """Generic audit logger invoked by every other service on mutations.

    Además de ``write`` (Ciclo 2), expone ``list`` y ``list_for_entity`` para
    la bitácora de auditoría (CU-31). Solo lectura — no altera el log.
    """

    async def write(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        action: str,
        entity_type: str,
        entity_id: UUID | None = None,
        actor_user_id: UUID | None = None,
        payload_diff: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        log = AuditLog(
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            payload_diff=payload_diff,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(log)
        await db.flush()
        return log

    def _apply_scope(
        self,
        query,
        *,
        exclude_sensitive: bool,
        restrict_to_actor: UUID | None,
    ):
        if restrict_to_actor is not None:
            query = query.where(AuditLog.actor_user_id == restrict_to_actor)
        if exclude_sensitive:
            for prefix in _SENSITIVE_PREFIXES:
                query = query.where(~AuditLog.action.like(f"{prefix}%"))
        return query

    async def list(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        entity_type: str | None = None,
        entity_id: UUID | None = None,
        actor_user_id: UUID | None = None,
        action: str | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        exclude_sensitive: bool = False,
        restrict_to_actor: UUID | None = None,
        page: int = 1,
        limit: int = 50,
    ) -> tuple[list[AuditLog], int]:
        """Paginated audit-log query filtered by tenant + optional facets + role scope."""
        query = select(AuditLog).where(AuditLog.tenant_id == tenant_id)

        if entity_type:
            query = query.where(AuditLog.entity_type == entity_type)
        if entity_id is not None:
            query = query.where(AuditLog.entity_id == entity_id)
        if actor_user_id is not None:
            query = query.where(AuditLog.actor_user_id == actor_user_id)
        if action:
            query = query.where(AuditLog.action == action)
        if from_date:
            query = query.where(AuditLog.created_at >= datetime.combine(from_date, time.min))
        if to_date:
            query = query.where(AuditLog.created_at <= datetime.combine(to_date, time.max))

        query = self._apply_scope(
            query,
            exclude_sensitive=exclude_sensitive,
            restrict_to_actor=restrict_to_actor,
        )

        count_q = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_q)).scalar_one()

        offset = (page - 1) * limit
        query = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all()), total

    async def list_for_entity(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        entity_type: str,
        entity_id: UUID,
        exclude_sensitive: bool = False,
        restrict_to_actor: UUID | None = None,
        page: int = 1,
        limit: int = 50,
    ) -> tuple[list[AuditLog], int]:
        """Chronological audit trail for a single entity (CU-31 vista por entidad)."""
        return await self.list(
            db,
            tenant_id=tenant_id,
            entity_type=entity_type,
            entity_id=entity_id,
            exclude_sensitive=exclude_sensitive,
            restrict_to_actor=restrict_to_actor,
            page=page,
            limit=limit,
        )


audit_service = AuditService()
