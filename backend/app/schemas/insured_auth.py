"""Pydantic schemas para el canal asegurado (CU-01)."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class InsuredLoginPayload(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)
    tenant_slug: str = Field(min_length=1, max_length=100)


class InsuredRegisterPayload(BaseModel):
    """Registro inicial del asegurado con el activation_token de la invitación."""

    activation_token: str = Field(min_length=10, max_length=64)
    password: str = Field(min_length=8, max_length=128)


class InsuredForgotPasswordPayload(BaseModel):
    email: EmailStr
    tenant_slug: str = Field(min_length=1, max_length=100)


class InsuredResetPasswordPayload(BaseModel):
    token: str = Field(min_length=10, max_length=64)
    new_password: str = Field(min_length=8, max_length=128)


class InsuredRefreshPayload(BaseModel):
    refresh_token: str


class InsuredLogoutPayload(BaseModel):
    refresh_token: str


class DeviceTokenPayload(BaseModel):
    expo_push_token: str = Field(min_length=1, max_length=255)
    platform: str = Field(pattern="^(ios|android)$")


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    policyholder_id: UUID
    tenant_id: UUID
    is_active: bool
    mfa_enabled: bool


class InsuredTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    account: AccountOut


class InsuredAccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class InviteResponse(BaseModel):
    """Respuesta del endpoint de invitación (CU-01 F-A1). Devuelve el token en claro
    porque NO se envía mail en el alcance del Ciclo 7 (decisión del usuario)."""

    account_id: UUID
    activation_token: str
    activation_expires_at: str
    email: str
