"""Pydantic schemas for claims (expedientes)."""

from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.claim_request import ClaimRequestOut


class PolicyholderSnippet(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    full_name: str
    document_id: str
    phone: str | None = None


class PolicySnippet(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    policy_number: str
    coverage_type: str
    valid_from: date
    valid_to: date


class VehicleSnippet(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    plate: str
    make: str
    model: str
    year: int


class ClaimOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    claim_number: str
    claim_request_id: UUID | None
    policyholder_id: UUID
    policy_id: UUID
    vehicle_id: UUID
    policyholder: PolicyholderSnippet | None = None
    policy: PolicySnippet | None = None
    vehicle: VehicleSnippet | None = None
    status: str
    source: str
    accident_date: date
    accident_time: time | None
    accident_location: str
    accident_lat: Decimal | None
    accident_lng: Decimal | None
    accident_description: str | None
    reported_damages: str | None
    created_by_user_id: UUID | None
    assigned_analyst_id: UUID | None
    supervisor_id: UUID | None
    fraud_score: Decimal | None
    decision: str | None
    decision_reason: str | None
    decided_by_user_id: UUID | None
    decided_at: datetime | None
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime | None


class ClaimCreate(BaseModel):
    policyholder_id: UUID
    policy_id: UUID
    vehicle_id: UUID
    accident_date: date
    accident_time: time | None = None
    accident_location: str = Field(min_length=3, max_length=500)
    accident_lat: Decimal | None = None
    accident_lng: Decimal | None = None
    accident_description: str | None = None
    reported_damages: str | None = None


class ClaimUpdate(BaseModel):
    policyholder_id: UUID | None = None
    policy_id: UUID | None = None
    vehicle_id: UUID | None = None
    accident_date: date | None = None
    accident_time: time | None = None
    accident_location: str | None = None
    accident_lat: Decimal | None = None
    accident_lng: Decimal | None = None
    accident_description: str | None = None
    reported_damages: str | None = None


class ClaimStatusUpdate(BaseModel):
    new_status: str
    reason: str | None = Field(default=None, max_length=2000)


class ClaimListResponse(BaseModel):
    items: list[ClaimOut]
    total: int
    page: int
    limit: int


class FormalizeResponse(BaseModel):
    claim: ClaimOut
    request: ClaimRequestOut | None = None


class ClaimAssign(BaseModel):
    analyst_user_id: UUID
    reason: str | None = Field(default=None, max_length=500)


class ClaimEscalate(BaseModel):
    supervisor_user_id: UUID
    reason: str = Field(min_length=1, max_length=2000)


class ClaimDecisionCreate(BaseModel):
    decision: str = Field(pattern="^(approved|rejected)$")
    reason: str = Field(min_length=1, max_length=2000)
