"""Pydantic schemas for third parties."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ThirdPartyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    claim_id: UUID
    kind: str
    full_name: str
    document_id: str | None
    contact_phone: str | None
    vehicle_plate: str | None
    vehicle_info: str | None
    statement: str | None
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime | None


class ThirdPartyCreate(BaseModel):
    kind: str = Field(min_length=1, max_length=50)
    full_name: str = Field(min_length=3, max_length=200)
    document_id: str | None = None
    contact_phone: str | None = None
    vehicle_plate: str | None = None
    vehicle_info: str | None = None
    statement: str | None = None


class ThirdPartyUpdate(BaseModel):
    kind: str | None = None
    full_name: str | None = Field(default=None, min_length=3, max_length=200)
    document_id: str | None = None
    contact_phone: str | None = None
    vehicle_plate: str | None = None
    vehicle_info: str | None = None
    statement: str | None = None


class ThirdPartyListResponse(BaseModel):
    items: list[ThirdPartyOut]
    total: int
    page: int
    limit: int
