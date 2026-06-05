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


# ── Vistas del canal asegurado (CU-06) ─────────────────────────────────
# Schemas DEDICADOS (no reuso de ClaimOut). Ocultan por diseño: fraud_score,
# created_by/assigned_analyst/supervisor/decided_by, y observaciones internas.


class PublicObservationOut(BaseModel):
    """Observación visible al asegurado (is_internal == False)."""

    model_config = ConfigDict(from_attributes=True)
    id: UUID
    comment: str
    created_at: datetime


class InsuredDocumentRequestOut(BaseModel):
    """Solicitud de documentación tal como la ve el asegurado (CU-07/08)."""

    model_config = ConfigDict(from_attributes=True)
    id: UUID
    description: str
    status: str
    created_at: datetime
    resolved_at: datetime | None = None


class InsuredTimelineEntry(BaseModel):
    """Hito del historial de estados, sin datos internos (sin actor ni motivo interno)."""

    to_status: str
    created_at: datetime


class ClaimOutInsured(BaseModel):
    """Vista del expediente para el asegurado. Solo campos no sensibles."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    claim_number: str
    status: str
    source: str
    accident_date: date
    accident_time: time | None
    accident_location: str
    accident_lat: Decimal | None
    accident_lng: Decimal | None
    accident_description: str | None
    reported_damages: str | None
    decision: str | None
    decision_reason: str | None
    decided_at: datetime | None
    created_at: datetime
    updated_at: datetime | None
    # Relacionados que el asegurado posee:
    policyholder: PolicyholderSnippet | None = None
    policy: PolicySnippet | None = None
    vehicle: VehicleSnippet | None = None
    # Detalle expandido (poblado por el service, no por ORM lazy-load):
    observations: list[PublicObservationOut] = []
    document_requests: list[InsuredDocumentRequestOut] = []
    timeline: list[InsuredTimelineEntry] = []


class InsuredClaimRequestListItem(BaseModel):
    """Item de la lista unificada 'Mis reclamos' (CU-06)."""

    model_config = ConfigDict(from_attributes=True)
    id: UUID
    request_number: str | None
    status: str
    accident_date: date | None
    accident_location: str | None
    formalized_claim_id: UUID | None
    intake_decision_reason: str | None
    created_at: datetime


class InsuredClaimRequestListResponse(BaseModel):
    items: list[InsuredClaimRequestListItem]
    total: int
    page: int
    limit: int
