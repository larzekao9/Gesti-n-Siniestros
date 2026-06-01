"""Pydantic schemas for claim requests (solicitudes)."""

from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ClaimRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    request_number: str | None
    status: str
    policyholder_id: UUID
    policy_id: UUID
    vehicle_id: UUID
    accident_date: date | None
    accident_time: time | None
    accident_location: str | None
    accident_lat: Decimal | None
    accident_lng: Decimal | None
    accident_description: str | None
    reported_damages: str | None
    submitted_at: datetime | None
    reviewed_by_user_id: UUID | None
    intake_decision_reason: str | None
    formalized_claim_id: UUID | None
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime | None


class ClaimRequestCreate(BaseModel):
    policyholder_id: UUID
    policy_id: UUID
    vehicle_id: UUID
    accident_date: date | None = None
    accident_time: time | None = None
    accident_location: str | None = None
    accident_lat: Decimal | None = None
    accident_lng: Decimal | None = None
    accident_description: str | None = None
    reported_damages: str | None = None


class ClaimRequestUpdate(BaseModel):
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


class ClaimRequestListResponse(BaseModel):
    items: list[ClaimRequestOut]
    total: int
    page: int
    limit: int


class RejectIntakePayload(BaseModel):
    reason: str = Field(min_length=20, max_length=2000)


class ReassignPayload(BaseModel):
    target_user_id: UUID
