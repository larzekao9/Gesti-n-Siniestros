"""Notification domain service — CU-27 notification infrastructure."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationKind
from app.services.exceptions import NotFoundError


class NotificationService:
    """Creates, lists, and marks notifications as read."""

    async def create(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        recipient_user_id: UUID | None = None,
        recipient_account_id: UUID | None = None,
        entity_type: str,
        entity_id: UUID | None = None,
        kind: NotificationKind,
        title: str,
        body: str,
        push_data: dict | None = None,
    ) -> Notification:
        if not recipient_user_id and not recipient_account_id:
            # At least one recipient must be set
            return None  # silently skip — nothing to notify

        notification = Notification(
            tenant_id=tenant_id,
            recipient_user_id=recipient_user_id,
            recipient_account_id=recipient_account_id,
            entity_type=entity_type,
            entity_id=entity_id,
            kind=kind,
            title=title,
            body=body,
        )
        db.add(notification)
        await db.flush()

        # Despacho push best-effort al asegurado (Ciclo 7). Fire-and-forget: el
        # PushService nunca lanza, así que no afecta la transacción de negocio.
        if recipient_account_id is not None:
            from app.services.push_service import push_service

            await push_service.send(
                db,
                tenant_id=tenant_id,
                account_id=recipient_account_id,
                title=title,
                body=body,
                data=push_data or {"entity_type": entity_type, "entity_id": str(entity_id) if entity_id else None},
            )

        return notification

    async def list_for_account(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        recipient_account_id: UUID,
        unread_only: bool = False,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Notification], int, int]:
        query = select(Notification).where(
            Notification.tenant_id == tenant_id,
            Notification.recipient_account_id == recipient_account_id,
        )
        if unread_only:
            query = query.where(Notification.read_at.is_(None))

        count_q = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_q)).scalar_one()

        unread_q = select(func.count()).select_from(
            select(Notification).where(
                Notification.tenant_id == tenant_id,
                Notification.recipient_account_id == recipient_account_id,
                Notification.read_at.is_(None),
            ).subquery()
        )
        unread_count = (await db.execute(unread_q)).scalar_one()

        offset = (page - 1) * limit
        query = query.order_by(Notification.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all()), total, unread_count

    async def mark_read_for_account(
        self,
        db: AsyncSession,
        *,
        notification_id: UUID,
        tenant_id: UUID,
        recipient_account_id: UUID,
    ) -> Notification:
        result = await db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.tenant_id == tenant_id,
                Notification.recipient_account_id == recipient_account_id,
            )
        )
        notification = result.scalar_one_or_none()
        if notification is None:
            raise NotFoundError("Notificación no encontrada")

        notification.read_at = datetime.now(timezone.utc)
        await db.flush()
        await db.refresh(notification)
        return notification

    async def list_for_recipient(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        recipient_user_id: UUID,
        unread_only: bool = False,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Notification], int, int]:
        query = select(Notification).where(
            Notification.tenant_id == tenant_id,
            Notification.recipient_user_id == recipient_user_id,
        )
        if unread_only:
            query = query.where(Notification.read_at.is_(None))

        count_q = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_q)).scalar_one()

        unread_q = select(func.count()).select_from(
            select(Notification).where(
                Notification.tenant_id == tenant_id,
                Notification.recipient_user_id == recipient_user_id,
                Notification.read_at.is_(None),
            ).subquery()
        )
        unread_count = (await db.execute(unread_q)).scalar_one()

        offset = (page - 1) * limit
        query = query.order_by(Notification.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all()), total, unread_count

    async def mark_read(
        self,
        db: AsyncSession,
        *,
        notification_id: UUID,
        tenant_id: UUID,
        recipient_user_id: UUID,
    ) -> Notification:
        result = await db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.tenant_id == tenant_id,
                Notification.recipient_user_id == recipient_user_id,
            )
        )
        notification = result.scalar_one_or_none()
        if notification is None:
            raise NotFoundError("Notificación no encontrada")

        notification.read_at = datetime.now(timezone.utc)
        await db.flush()
        # Refresh para que `updated_at` (onupdate=func.now()) quede poblado
        # en el objeto y Pydantic no intente lazy-load fuera de contexto async.
        await db.refresh(notification)
        return notification

    async def mark_all_read(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        recipient_user_id: UUID,
    ) -> int:
        result = await db.execute(
            update(Notification)
            .where(
                Notification.tenant_id == tenant_id,
                Notification.recipient_user_id == recipient_user_id,
                Notification.read_at.is_(None),
            )
            .values(read_at=datetime.now(timezone.utc))
        )
        await db.flush()
        return result.rowcount

    async def mark_all_read_for_account(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        recipient_account_id: UUID,
    ) -> int:
        result = await db.execute(
            update(Notification)
            .where(
                Notification.tenant_id == tenant_id,
                Notification.recipient_account_id == recipient_account_id,
                Notification.read_at.is_(None),
            )
            .values(read_at=datetime.now(timezone.utc))
        )
        await db.flush()
        return result.rowcount


notification_service = NotificationService()
