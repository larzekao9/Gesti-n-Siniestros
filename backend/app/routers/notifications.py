"""Notification router — CU-27 internal notification endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.notification import NotificationListResponse, NotificationOut
from app.services.notification_service import notification_service
from app.services.exceptions import NotFoundError

router = APIRouter(prefix="/me/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        items, total, unread_count = await notification_service.list_for_recipient(
            db,
            tenant_id=current_user.tenant_id,
            recipient_user_id=current_user.id,
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
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{notification_id}", response_model=NotificationOut)
async def mark_notification_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        notification = await notification_service.mark_read(
            db,
            notification_id=notification_id,
            tenant_id=current_user.tenant_id,
            recipient_user_id=current_user.id,
        )
        await db.commit()
        return NotificationOut.model_validate(notification)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/mark-all-read")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count = await notification_service.mark_all_read(
        db,
        tenant_id=current_user.tenant_id,
        recipient_user_id=current_user.id,
    )
    await db.commit()
    return {"marked_read": count}
