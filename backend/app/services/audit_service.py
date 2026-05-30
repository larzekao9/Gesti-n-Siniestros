"""Audit log domain service — system-wide traceability."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditService:
    """Generic audit logger invoked by every other service on mutations."""

    async def write(
        self,
        db: AsyncSession,
        *,
        action: str,
        entity_type: str,
        entity_id: UUID | None = None,
        actor_user_id: UUID | None = None,
        payload_diff: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        log = AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            payload_diff=payload_diff,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(log)
        # flush to get the server-default tenant_id populated if using TenantMixin
        await db.flush()
        return log
