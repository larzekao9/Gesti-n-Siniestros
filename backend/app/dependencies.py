"""FastAPI dependency functions for auth and multi-tenancy."""

from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models.policyholder_account import PolicyholderAccount
from app.models.tenant import Tenant
from app.models.user import Role, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
insured_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/insured-auth/login")


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

    # Retro-compat: un token sin claim `scope` se trata como 'internal'.
    # Un token de asegurado (scope='insured') NO puede usar endpoints internos.
    if payload.get("scope", "internal") != "internal":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de canal asegurado no válido para esta operación",
            headers={"WWW-Authenticate": "Bearer"},
        )

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


class AuditScope:
    """Resolved audit-log visibility for the current user (CU-31).

    - ``admin``: vista global, todos los eventos (incluidos los sensibles).
    - ``supervisor``: eventos del tenant, ocultando los sensibles (LOGIN/PASSWORD/MFA).
    - ``analyst``: solo su propia actividad (``actor_user_id == self``), sin sensibles.
    """

    def __init__(self, user: User) -> None:
        self.user = user
        if user.role == Role.ADMIN:
            self.exclude_sensitive = False
            self.restrict_to_actor: UUID | None = None
        elif user.role == Role.SUPERVISOR:
            self.exclude_sensitive = True
            self.restrict_to_actor = None
        else:  # ANALYST
            self.exclude_sensitive = True
            self.restrict_to_actor = user.id


def require_audit_access(
    current_user: User = Depends(get_current_user),
) -> AuditScope:
    """Return the audit visibility scope for the authenticated user (CU-31).

    Cualquier usuario interno autenticado puede consultar la bitácora, pero el
    alcance de lo que ve depende de su rol (ver :class:`AuditScope`).
    """
    return AuditScope(current_user)


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


# ── Canal asegurado (Ciclo 7) ─────────────────────────────────────────


async def get_current_account(
    token: str = Depends(insured_oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> PolicyholderAccount:
    """Resuelve y valida el JWT del asegurado (``scope='insured'``) → ``PolicyholderAccount``.

    Raises:
        HTTPException: 401 si el token es inválido, el scope no es 'insured',
            la cuenta no existe o está inactiva.
    """
    payload = decode_token(token)

    if payload.get("scope") != "insured":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere un token del canal asegurado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    account_id_raw: str | None = payload.get("sub")
    tenant_id_raw: str | None = payload.get("tenant_id")

    if account_id_raw is None or tenant_id_raw is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token con claims insuficientes",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        account_id = UUID(account_id_raw)
        tenant_id = UUID(tenant_id_raw)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Claims de token inválidos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(
        select(PolicyholderAccount).where(
            PolicyholderAccount.id == account_id,
            PolicyholderAccount.tenant_id == tenant_id,
        )
    )
    account = result.scalar_one_or_none()

    if account is None or not account.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cuenta no encontrada o inactiva",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return account


class Principal:
    """Identidad autenticada que puede ser un ``User`` interno o un asegurado.

    Permite que endpoints compartidos por ambos canales (p.ej.
    ``/api/me/notifications``) despachen según el tipo de principal sin acoplar
    la lógica a un solo scope.
    """

    def __init__(
        self, *, user: User | None = None, account: PolicyholderAccount | None = None
    ) -> None:
        self.user = user
        self.account = account

    @property
    def is_account(self) -> bool:
        return self.account is not None

    @property
    def tenant_id(self) -> UUID:
        return self.account.tenant_id if self.is_account else self.user.tenant_id


async def get_current_principal(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Principal:
    """Resuelve el principal (interno o asegurado) según el ``scope`` del JWT.

    Token sin scope o ``scope='internal'`` → ``User``. ``scope='insured'`` →
    ``PolicyholderAccount``. Reutiliza la validación de ``get_current_user`` /
    ``get_current_account`` según corresponda.
    """
    payload = decode_token(token)
    if payload.get("scope") == "insured":
        account = await get_current_account(token=token, db=db)
        return Principal(account=account)
    user = await get_current_user(token=token, db=db)
    return Principal(user=user)
