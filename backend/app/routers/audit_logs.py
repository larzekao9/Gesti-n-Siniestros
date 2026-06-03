"""Audit log router — CU-31 traceability views (read-only)."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import AuditScope, require_audit_access
from app.schemas.audit import AuditLogListResponse, AuditLogOut
from app.services.audit_service import audit_service

router = APIRouter(prefix="/audit-logs", tags=["audit"])


@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    entity_type: str | None = Query(None),
    entity_id: UUID | None = Query(None),
    actor: UUID | None = Query(None),
    action: str | None = Query(None),
    from_: date | None = Query(None, alias="from"),
    to: date | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    scope: AuditScope = Depends(require_audit_access),
    db: AsyncSession = Depends(get_db),
) -> AuditLogListResponse:
    """Consulta la bitácora de auditoría con filtros + alcance por rol.

    Vista por entidad: pasar ``entity_type`` + ``entity_id``.
    Vista global (admin): omitir esos parámetros y filtrar por actor/action/fecha.
    """
    items, total = await audit_service.list(
        db,
        tenant_id=scope.user.tenant_id,
        entity_type=entity_type,
        entity_id=entity_id,
        actor_user_id=actor,
        action=action,
        from_date=from_,
        to_date=to,
        exclude_sensitive=scope.exclude_sensitive,
        restrict_to_actor=scope.restrict_to_actor,
        page=page,
        limit=limit,
    )
    return AuditLogListResponse(
        items=[AuditLogOut.model_validate(log) for log in items],
        total=total,
        page=page,
        limit=limit,
    )
