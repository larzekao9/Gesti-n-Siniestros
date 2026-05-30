"""Pydantic schemas for vehicle CRUD."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class VehicleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    plate: str
    make: str
    model: str
    year: int
    color: str | None
    vehicle_type: str
    policy_id: UUID
    status: str
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime | None


class VehicleCreate(BaseModel):
    plate: str = Field(min_length=4, max_length=20)
    make: str = Field(min_length=1, max_length=50)
    model: str = Field(min_length=1, max_length=50)
    year: int = Field(ge=1900, le=2100)
    color: str | None = None
    vehicle_type: str = "sedan"
    policy_id: UUID


class VehicleUpdate(BaseModel):
    make: str | None = Field(default=None, min_length=1, max_length=50)
    model: str | None = Field(default=None, min_length=1, max_length=50)
    year: int | None = Field(default=None, ge=1900, le=2100)
    color: str | None = None
    vehicle_type: str | None = None
    policy_id: UUID | None = None
    status: str | None = None


class VehicleListResponse(BaseModel):
    items: list[VehicleOut]
    total: int
    page: int
    limit: int
