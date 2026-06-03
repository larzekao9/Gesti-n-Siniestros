"""Reports router — CU-22 operational report download (PDF / Excel)."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import require_role
from app.models.user import Role, User
from app.services.report_service import report_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/claims")
async def generate_claims_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    from_: date | None = Query(None, alias="from"),
    to: date | None = Query(None),
    status_: str | None = Query(None, alias="status"),
    analyst: str | None = Query(None),
    current_user: User = require_role(Role.SUPERVISOR, Role.ADMIN),
    db: AsyncSession = Depends(get_db),
) -> Response:
    try:
        content, media_type, filename = await report_service.build_claims_report(
            db,
            tenant_id=current_user.tenant_id,
            actor_user_id=current_user.id,
            report_format=format,
            from_date=from_,
            to_date=to,
            status=status_,
            analyst_id=analyst,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    await db.commit()
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
