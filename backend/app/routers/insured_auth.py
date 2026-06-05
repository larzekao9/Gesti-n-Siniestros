"""Insured auth router (canal asegurado — CU-01).

Solo orquesta: parsea el request, delega en ``InsuredAuthService`` y traduce las
excepciones de dominio a HTTP. Sin lógica de negocio.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_account
from app.models.policyholder_account import PolicyholderAccount
from app.schemas.insured_auth import (
    AccountOut,
    DeviceTokenPayload,
    InsuredAccessTokenResponse,
    InsuredForgotPasswordPayload,
    InsuredLoginPayload,
    InsuredLogoutPayload,
    InsuredRefreshPayload,
    InsuredRegisterPayload,
    InsuredResetPasswordPayload,
    InsuredTokenResponse,
)
from app.services.exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.services.insured_auth_service import insured_auth_service

router = APIRouter(prefix="/insured-auth", tags=["insured-auth"])


def _raise_domain(exc: Exception) -> None:
    if isinstance(exc, AuthenticationError):
        raise HTTPException(status_code=401, detail=str(exc))
    if isinstance(exc, NotFoundError):
        raise HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, ConflictError):
        raise HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, ValidationError):
        raise HTTPException(status_code=422, detail=str(exc))
    raise exc


@router.post("/login", response_model=InsuredTokenResponse)
async def login(payload: InsuredLoginPayload, db: AsyncSession = Depends(get_db)):
    try:
        result = await insured_auth_service.login(
            db,
            email=payload.email,
            password=payload.password,
            tenant_slug=payload.tenant_slug,
        )
        await db.commit()
        return result
    except (AuthenticationError, NotFoundError, ConflictError, ValidationError) as e:
        await db.rollback()
        _raise_domain(e)


@router.post("/register", response_model=InsuredTokenResponse)
async def register(payload: InsuredRegisterPayload, db: AsyncSession = Depends(get_db)):
    try:
        result = await insured_auth_service.register_with_token(
            db,
            activation_token=payload.activation_token,
            password=payload.password,
        )
        await db.commit()
        return result
    except (AuthenticationError, NotFoundError, ConflictError, ValidationError) as e:
        await db.rollback()
        _raise_domain(e)


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    payload: InsuredForgotPasswordPayload, db: AsyncSession = Depends(get_db)
):
    try:
        await insured_auth_service.request_password_reset(
            db, email=payload.email, tenant_slug=payload.tenant_slug
        )
        await db.commit()
    except NotFoundError:
        # No filtrar existencia del tenant/email — responder 200 igual.
        await db.rollback()
    return {"message": "Si el email existe, se enviaron instrucciones"}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    payload: InsuredResetPasswordPayload, db: AsyncSession = Depends(get_db)
):
    try:
        await insured_auth_service.confirm_password_reset(
            db, token=payload.token, new_password=payload.new_password
        )
        await db.commit()
        return {"message": "Contraseña actualizada"}
    except (ValidationError, NotFoundError) as e:
        await db.rollback()
        _raise_domain(e)


@router.post("/refresh", response_model=InsuredAccessTokenResponse)
async def refresh(payload: InsuredRefreshPayload, db: AsyncSession = Depends(get_db)):
    try:
        result = await insured_auth_service.refresh(db, payload.refresh_token)
        await db.commit()
        return result
    except AuthenticationError as e:
        await db.rollback()
        _raise_domain(e)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(payload: InsuredLogoutPayload, db: AsyncSession = Depends(get_db)):
    await insured_auth_service.logout(db, payload.refresh_token)
    await db.commit()
    return {"message": "Sesión cerrada"}


@router.get("/me", response_model=AccountOut)
async def me(account: PolicyholderAccount = Depends(get_current_account)):
    return account


@router.post("/register-device-token", status_code=status.HTTP_201_CREATED)
async def register_device_token(
    payload: DeviceTokenPayload,
    account: PolicyholderAccount = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    try:
        device = await insured_auth_service.register_device_token(
            db,
            account=account,
            expo_push_token=payload.expo_push_token,
            platform=payload.platform,
        )
        await db.commit()
        return {"id": str(device.id), "platform": device.platform.value}
    except ValidationError as e:
        await db.rollback()
        _raise_domain(e)


@router.post("/unregister-device-token", status_code=status.HTTP_200_OK)
async def unregister_device_token(
    payload: DeviceTokenPayload,
    account: PolicyholderAccount = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    await insured_auth_service.unregister_device_token(
        db, account=account, expo_push_token=payload.expo_push_token
    )
    await db.commit()
    return {"message": "Dispositivo desregistrado"}
