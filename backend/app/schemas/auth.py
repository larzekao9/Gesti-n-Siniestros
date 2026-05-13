"""Pydantic v2 schemas for auth request and response payloads."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    """Payload for registering a new user under an existing tenant."""

    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2)
    tenant_slug: str


class LoginRequest(BaseModel):
    """Payload for authenticating a user. ``mfa_code`` is only required when
    MFA has been enabled on the account."""

    email: EmailStr
    password: str
    mfa_code: str | None = None


class RefreshRequest(BaseModel):
    """Payload for rotating a refresh token."""

    refresh_token: str


class MFAVerifyRequest(BaseModel):
    """Payload for activating MFA by verifying a TOTP code."""

    code: str = Field(min_length=6, max_length=6)


class UserResponse(BaseModel):
    """Public representation of a user account."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    role: str
    mfa_enabled: bool
    tenant_id: UUID


class TokenResponse(BaseModel):
    """Response returned after a successful login or registration."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class MFASetupResponse(BaseModel):
    """Response returned when initiating MFA setup."""

    secret: str
    qr_uri: str
