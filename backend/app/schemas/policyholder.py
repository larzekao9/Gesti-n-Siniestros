"""Pydantic schemas for policyholder CRUD."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PolicyholderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: str
    full_name: str
    phone: str
    email: str | None
    address: str | None
    status: str
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime | None


class PolicyholderCreate(BaseModel):
    document_id: str = Field(min_length=3, max_length=20)
    full_name: str = Field(min_length=2, max_length=200)
    phone: str = Field(min_length=7, max_length=20)
    email: str | None = None
    address: str | None = None


class PolicyholderUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=200)
    phone: str | None = Field(default=None, min_length=7, max_length=20)
    email: str | None = None
    address: str | None = None
    status: str | None = None


class PolicyholderListResponse(BaseModel):
    items: list[PolicyholderOut]
    total: int
    page: int
    limit: int
