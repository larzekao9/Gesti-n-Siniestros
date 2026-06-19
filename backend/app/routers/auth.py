"""Authentication router: register, login, refresh, logout, MFA setup/verify."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.limiter import limiter
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    MFASetupResponse,
    MFAVerifyRequest,
    PasswordChangeRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthService
from app.services.exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)

router = APIRouter(prefix="/auth", tags=["auth"])

auth_service = AuthService()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=TokenResponse,
)
@limiter.limit("5/minute")  # DT-10: anti-abuso/anti-fuerza bruta
async def register(
    request: Request,
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    try:
        result = await auth_service.register(
            db,
            email=body.email,
            password=body.password,
            full_name=body.full_name,
            tenant_slug=body.tenant_slug,
        )
        return TokenResponse(**result)
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# response_model=None: el login puede devolver TokenResponse (éxito) o el dict
# {"mfa_required": true} (cuando falta el código TOTP). Forzar response_model a
# TokenResponse hacía 500 en el caso MFA porque el dict no valida contra él (DT-24).
@router.post("/login", response_model=None)
@limiter.limit("5/minute")  # DT-10: anti-abuso/anti-fuerza bruta
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse | dict:
    tenant_slug = request.headers.get("X-Tenant-Slug")
    if not tenant_slug:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cabecera X-Tenant-Slug requerida",
        )

    try:
        result = await auth_service.login(
            db,
            email=body.email,
            password=body.password,
            tenant_slug=tenant_slug,
            mfa_code=body.mfa_code,
        )
        if "mfa_required" in result:
            return result
        return TokenResponse(**result)
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/refresh")
async def refresh_token(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        return await auth_service.refresh(db, body.refresh_token)
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/logout")
async def logout(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    await auth_service.logout(db, body.refresh_token)
    return {"message": "ok"}


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    result = await auth_service.get_me(db, current_user)
    return UserResponse(**result)


@router.post("/mfa/setup", response_model=MFASetupResponse)
async def mfa_setup(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MFASetupResponse:
    result = await auth_service.setup_mfa(db, current_user)
    return MFASetupResponse(**result)


@router.post("/mfa/verify")
@limiter.limit("5/minute")  # DT-10: anti-abuso/anti-fuerza bruta
async def mfa_verify(
    request: Request,
    body: MFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        await auth_service.verify_mfa(db, current_user, body.code)
        return {"message": "MFA activado"}
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ---------------------------------------------------------------------------
# Password reset / change (CU-28, CU-29)
# ---------------------------------------------------------------------------


@router.post("/password-reset/request", status_code=status.HTTP_200_OK)
async def request_password_reset(
    body: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    await auth_service.request_password_reset(
        db, email=body.email, tenant_slug=body.tenant_slug
    )
    return {"message": "Si el email existe, recibirás un enlace para restablecer tu contraseña"}


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    body: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        await auth_service.confirm_password_reset(
            db, token=body.token, new_password=body.new_password
        )
        return {"message": "Contraseña restablecida correctamente"}
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/password-change")
async def change_password(
    body: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        await auth_service.change_password(
            db,
            current_user,
            current_password=body.current_password,
            new_password=body.new_password,
        )
        return {"message": "Contraseña cambiada correctamente"}
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
