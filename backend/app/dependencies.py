"""FastAPI dependency functions for auth and multi-tenancy."""

from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models.tenant import Tenant
from app.models.user import Role, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate the JWT, then return the authenticated ``User``.

    Args:
        token: Bearer JWT provided by the client.
        db: Async database session.

    Returns:
        The active ``User`` instance identified by the token.

    Raises:
        HTTPException: 401 if the token is invalid, the user does not exist,
            or the account is inactive.
    """
    payload = decode_token(token)

    user_id_raw: str | None = payload.get("sub")
    tenant_id_raw: str | None = payload.get("tenant_id")

    if user_id_raw is None or tenant_id_raw is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token con claims insuficientes",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = UUID(user_id_raw)
        tenant_id = UUID(tenant_id_raw)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Claims de token inválidos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(
        select(User).where(User.id == user_id, User.tenant_id == tenant_id)
    )
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_tenant(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Tenant:
    """Return the ``Tenant`` associated with the current authenticated user.

    Args:
        current_user: The authenticated user.
        db: Async database session.

    Returns:
        The active ``Tenant`` instance.

    Raises:
        HTTPException: 404 if the tenant no longer exists.
        HTTPException: 403 if the tenant is inactive.
    """
    result = await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))
    tenant = result.scalar_one_or_none()

    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant no encontrado",
        )

    if not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant inactivo",
        )

    return tenant


def require_role(*roles: Role) -> Depends:
    """Return a FastAPI dependency that enforces one of the given roles.

    Args:
        *roles: Accepted ``Role`` values. The current user must have at least
            one of them.

    Returns:
        A ``Depends`` instance suitable for use in path-operation signatures.

    Example::

        @router.get("/admin-only")
        async def admin_only(user: User = require_role(Role.ADMIN)):
            ...
    """

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permisos insuficientes",
            )
        return current_user

    return Depends(dependency)
