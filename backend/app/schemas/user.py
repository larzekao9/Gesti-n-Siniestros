"""Pydantic schemas for user CRUD."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import Role


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    role: Role
    is_active: bool
    mfa_enabled: bool
    tenant_id: UUID


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2)
    role: Role


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2)
    role: Role | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8)


class UserListResponse(BaseModel):
    items: list[UserOut]
    total: int
    page: int
    limit: int
