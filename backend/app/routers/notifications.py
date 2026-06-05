"""Notification router — CU-27.

Endpoint compartido por el canal interno (usuarios) y el canal asegurado
(``policyholder_accounts``, Ciclo 7). Despacha según el ``scope`` del token vía
``get_current_principal``.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import Principal, get_current_principal
from app.schemas.notification import NotificationListResponse, NotificationOut
from app.services.notification_service import notification_service
from app.services.exceptions import NotFoundError

router = APIRouter(prefix="/me/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    principal: Principal = Depends(get_current_principal),
    db: AsyncSession = Depends(get_db),
):
    if principal.is_account:
        items, total, unread_count = await notification_service.list_for_account(
            db,
            tenant_id=principal.tenant_id,
            recipient_account_id=principal.account.id,
            unread_only=unread_only,
            page=page,
            limit=limit,
        )
    else:
        items, total, unread_count = await notification_service.list_for_recipient(
            db,
            tenant_id=principal.tenant_id,
            recipient_user_id=principal.user.id,
            unread_only=unread_only,
            page=page,
            limit=limit,
        )
    return NotificationListResponse(
        items=[NotificationOut.model_validate(n) for n in items],
        total=total,
        page=page,
        limit=limit,
        unread_count=unread_count,
    )


@router.patch("/{notification_id}", response_model=NotificationOut)
async def mark_notification_read(
    notification_id: UUID,
    principal: Principal = Depends(get_current_principal),
    db: AsyncSession = Depends(get_db),
):
    try:
        if principal.is_account:
            notification = await notification_service.mark_read_for_account(
                db,
                notification_id=notification_id,
                tenant_id=principal.tenant_id,
                recipient_account_id=principal.account.id,
            )
        else:
            notification = await notification_service.mark_read(
                db,
                notification_id=notification_id,
                tenant_id=principal.tenant_id,
                recipient_user_id=principal.user.id,
            )
        await db.commit()
        return NotificationOut.model_validate(notification)
    except NotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/mark-all-read")
async def mark_all_notifications_read(
    principal: Principal = Depends(get_current_principal),
    db: AsyncSession = Depends(get_db),
):
    if principal.is_account:
        count = await notification_service.mark_all_read_for_account(
            db,
            tenant_id=principal.tenant_id,
            recipient_account_id=principal.account.id,
        )
    else:
        count = await notification_service.mark_all_read(
            db,
            tenant_id=principal.tenant_id,
            recipient_user_id=principal.user.id,
        )
    await db.commit()
    return {"marked_read": count}
