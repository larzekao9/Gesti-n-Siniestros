"""User management domain service."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import Role, User
from app.services.exceptions import ConflictError, NotFoundError, ValidationError


class UserService:
    """Admin CRUD for internal users."""

    async def list_users(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        page: int = 1,
        limit: int = 20,
        role: str | None = None,
        search: str | None = None,
    ) -> tuple[list[User], int]:
        offset = (page - 1) * limit
        query = select(User).where(User.tenant_id == tenant_id)

        if role:
            query = query.where(User.role == role)
        if search:
            pattern = f"%{search}%"
            query = query.where(
                (User.full_name.ilike(pattern)) | (User.email.ilike(pattern))
            )

        count_q = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_q)).scalar_one()

        query = query.order_by(User.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all()), total

    async def get_user(self, db: AsyncSession, *, user_id: UUID, tenant_id: UUID) -> User:
        result = await db.execute(
            select(User).where(User.id == user_id, User.tenant_id == tenant_id)
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise NotFoundError("Usuario no encontrado")
        return user

    async def create_user(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        email: str,
        password: str,
        full_name: str,
        role: Role,
    ) -> User:
        existing = await db.execute(
            select(User).where(User.email == email, User.tenant_id == tenant_id)
        )
        if existing.scalar_one_or_none() is not None:
            raise ConflictError("El email ya está registrado en este tenant")

        user = User(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            role=role,
            tenant_id=tenant_id,
        )
        db.add(user)
        await db.flush()
        return user

    async def update_user(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        tenant_id: UUID,
        full_name: str | None = None,
        role: Role | None = None,
        is_active: bool | None = None,
        password: str | None = None,
    ) -> User:
        user = await self.get_user(db, user_id=user_id, tenant_id=tenant_id)

        if is_active is False and user.role == Role.ADMIN:
            count = await db.execute(
                select(func.count()).where(
                    User.tenant_id == tenant_id,
                    User.role == Role.ADMIN,
                    User.is_active.is_(True),
                    User.id != user_id,
                )
            )
            if count.scalar_one() == 0:
                raise ValidationError("No se puede desactivar el último administrador")

        if role is not None:
            if role != Role.ADMIN and user.role == Role.ADMIN:
                count = await db.execute(
                    select(func.count()).where(
                        User.tenant_id == tenant_id,
                        User.role == Role.ADMIN,
                        User.is_active.is_(True),
                        User.id != user_id,
                    )
                )
                if count.scalar_one() == 0:
                    raise ValidationError(
                        "No se puede cambiar el rol del último administrador"
                    )
            user.role = role

        if full_name is not None:
            user.full_name = full_name
        if is_active is not None:
            user.is_active = is_active
        if password is not None:
            user.hashed_password = hash_password(password)

        await db.flush()
        await db.refresh(user)
        return user
