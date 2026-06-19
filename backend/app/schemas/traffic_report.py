"""Traffic report Pydantic schemas."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class TrafficReportCreate(BaseModel):
    evidence_id: UUID | None = None
    officer_name: str | None = None
    report_code: str | None = None
    jurisdiction: str | None = None
    report_date: date | None = None
    summary: str | None = None


class TrafficReportUpdate(BaseModel):
    evidence_id: UUID | None = None
    officer_name: str | None = None
    report_code: str | None = None
    jurisdiction: str | None = None
    report_date: date | None = None
    summary: str | None = None


class TrafficReportOut(BaseModel):
    id: UUID
    tenant_id: UUID
    claim_id: UUID
    evidence_id: UUID | None = None
    officer_name: str | None = None
    report_code: str | None = None
    jurisdiction: str | None = None
    report_date: date | None = None
    summary: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class TrafficReportListResponse(BaseModel):
    items: list[TrafficReportOut]
    total: int
    page: int
    limit: int
