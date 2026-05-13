"""Authentication router: register, login, refresh, logout, MFA setup/verify."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_totp_secret,
    get_totp_uri,
    hash_password,
    verify_password,
    verify_totp,
)
from app.models.refresh_token import RefreshToken
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    MFASetupResponse,
    MFAVerifyRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# Reusable OAuth2 bearer extractor for endpoints that need a DB-session-aware
# current_user (avoids the session-sharing problem with Depends(get_current_user)).
_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _get_tenant_by_slug(slug: str, db: AsyncSession) -> Tenant:
    """Fetch a tenant by its slug or raise HTTP 404."""
    result = await db.execute(select(Tenant).where(Tenant.slug == slug))
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant '{slug}' no encontrado",
        )
    return tenant


async def _get_user_by_email_and_tenant(
    email: str, tenant_id: UUID, db: AsyncSession
) -> User | None:
    """Return a user matching email + tenant_id, or None."""
    result = await db.execute(
        select(User).where(User.email == email, User.tenant_id == tenant_id)
    )
    return result.scalar_one_or_none()


async def _persist_refresh_token(
    token: str, user: User, db: AsyncSession
) -> RefreshToken:
    """Persist a new refresh token record and return it."""
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    record = RefreshToken(
        token=token,
        user_id=user.id,
        tenant_id=user.tenant_id,
        expires_at=expires_at,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


def _build_token_response(user: User, refresh_token_str: str) -> TokenResponse:
    """Build a ``TokenResponse`` for the given authenticated user."""
    access_token = create_access_token(
        {"sub": str(user.id), "tenant_id": str(user.tenant_id)}
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_str,
        user=UserResponse.model_validate(user),
    )


async def _resolve_user_from_token(token: str, db: AsyncSession) -> User:
    """Decode a JWT and return the corresponding active User from the given session.

    Args:
        token: Raw bearer JWT string.
        db: The *same* AsyncSession that will be used for subsequent mutations.

    Returns:
        The active ``User`` ORM instance bound to ``db``.

    Raises:
        HTTPException: 401 if the token is invalid or the user is not found/active.
    """
    payload = decode_token(token)
    try:
        user_id = UUID(payload["sub"])
        tenant_id = UUID(payload["tenant_id"])
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token con claims insuficientes",
        )

    result = await db.execute(
        select(User).where(User.id == user_id, User.tenant_id == tenant_id)
    )
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo",
        )
    return user


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=TokenResponse,
)
async def register(
    request: Request,
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Register a new user under an existing tenant.

    Args:
        request: The incoming HTTP request.
        body: Registration payload.
        db: Async database session.

    Returns:
        A ``TokenResponse`` with access and refresh tokens.

    Raises:
        HTTPException: 404 if the tenant slug does not exist.
        HTTPException: 409 if the email is already registered in that tenant.
    """
    tenant = await _get_tenant_by_slug(body.tenant_slug, db)

    existing = await _get_user_by_email_and_tenant(body.email, tenant.id, db)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya está registrado en este tenant",
        )

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        tenant_id=tenant.id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    raw_refresh = create_refresh_token(
        {"sub": str(user.id), "tenant_id": str(user.tenant_id)}
    )
    await _persist_refresh_token(raw_refresh, user, db)

    return _build_token_response(user, raw_refresh)


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse | dict:
    """Authenticate a user with email, password, and optional MFA code.

    The tenant is resolved from the ``X-Tenant-Slug`` request header.

    Args:
        request: The incoming HTTP request.
        body: Login payload.
        db: Async database session.

    Returns:
        A ``TokenResponse`` on success, or ``{"mfa_required": true}`` when MFA
        is enabled but no TOTP code was supplied.

    Raises:
        HTTPException: 400 if the ``X-Tenant-Slug`` header is missing.
        HTTPException: 401 for invalid credentials or bad MFA code.
    """
    tenant_slug = request.headers.get("X-Tenant-Slug")
    if not tenant_slug:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cabecera X-Tenant-Slug requerida",
        )

    tenant = await _get_tenant_by_slug(tenant_slug, db)

    user = await _get_user_by_email_and_tenant(body.email, tenant.id, db)
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cuenta desactivada",
        )

    if user.mfa_enabled:
        if body.mfa_code is None:
            return {"mfa_required": True}
        if user.mfa_secret is None or not verify_totp(user.mfa_secret, body.mfa_code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Código MFA inválido",
            )

    raw_refresh = create_refresh_token(
        {"sub": str(user.id), "tenant_id": str(user.tenant_id)}
    )
    await _persist_refresh_token(raw_refresh, user, db)

    return _build_token_response(user, raw_refresh)


@router.post("/refresh")
async def refresh_token(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Rotate a refresh token and issue a new access token.

    The old refresh token is revoked upon successful rotation.

    Args:
        body: Payload containing the current refresh token.
        db: Async database session.

    Returns:
        A dict with ``access_token`` and ``token_type``.

    Raises:
        HTTPException: 401 if the token is invalid, expired, or already revoked.
    """
    decode_token(body.refresh_token)  # validates JWT signature and expiry

    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token == body.refresh_token)
    )
    db_token = result.scalar_one_or_none()

    if db_token is None or db_token.revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido o revocado",
        )

    # Guard against tokens stored without timezone info (SQLite stores naive datetimes)
    stored_exp = db_token.expires_at
    if stored_exp.tzinfo is None:
        stored_exp = stored_exp.replace(tzinfo=timezone.utc)
    if stored_exp < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expirado",
        )

    db_token.revoked = True
    await db.commit()

    result = await db.execute(select(User).where(User.id == db_token.user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo",
        )

    new_access = create_access_token(
        {"sub": str(user.id), "tenant_id": str(user.tenant_id)}
    )
    return {"access_token": new_access, "token_type": "bearer"}


@router.post("/logout")
async def logout(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Revoke a refresh token, effectively logging the user out.

    Args:
        body: Payload containing the refresh token to revoke.
        db: Async database session.

    Returns:
        A confirmation dict ``{"message": "ok"}``.
    """
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token == body.refresh_token)
    )
    db_token = result.scalar_one_or_none()
    if db_token is not None and not db_token.revoked:
        db_token.revoked = True
        await db.commit()

    return {"message": "ok"}


@router.post("/mfa/setup", response_model=MFASetupResponse)
async def mfa_setup(
    token: str = Depends(_oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> MFASetupResponse:
    """Generate a new TOTP secret and provisioning URI for the current user.

    MFA is *not* activated until the user confirms with a valid TOTP code via
    ``POST /auth/mfa/verify``.

    Args:
        token: Bearer JWT from the Authorization header.
        db: Async database session (shared for reads and the subsequent commit).

    Returns:
        A ``MFASetupResponse`` with the raw base32 secret and an otpauth:// URI.
    """
    current_user = await _resolve_user_from_token(token, db)

    secret = generate_totp_secret()
    current_user.mfa_secret = secret
    await db.commit()

    qr_uri = get_totp_uri(secret, current_user.email)
    return MFASetupResponse(secret=secret, qr_uri=qr_uri)


@router.post("/mfa/verify")
async def mfa_verify(
    body: MFAVerifyRequest,
    token: str = Depends(_oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Activate MFA by verifying a TOTP code against the stored secret.

    Args:
        body: Payload with the 6-digit TOTP code.
        token: Bearer JWT from the Authorization header.
        db: Async database session (shared for reads and the subsequent commit).

    Returns:
        A confirmation dict ``{"message": "MFA activado"}``.

    Raises:
        HTTPException: 400 if MFA setup has not been initiated.
        HTTPException: 400 if the TOTP code is invalid.
    """
    current_user = await _resolve_user_from_token(token, db)

    if current_user.mfa_secret is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA setup no iniciado. Llame primero a /auth/mfa/setup",
        )

    if not verify_totp(current_user.mfa_secret, body.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código TOTP inválido",
        )

    current_user.mfa_enabled = True
    await db.commit()

    return {"message": "MFA activado"}
