"""Pydantic schemas for dashboard analytics (CU-21)."""

from pydantic import BaseModel


class KPIsResponse(BaseModel):
    """Operational KPIs for the tenant dashboard (no AI metrics — Ciclo 8)."""

    total_claims: int
    total_requests: int
    claims_by_status: dict[str, int]
    requests_by_status: dict[str, int]
    intake_rejection_rate: float  # rejected_at_intake / total_requests
    approval_rate: float  # approved / (approved + rejected)
    avg_days_to_decision: float | None  # mean days registered → decided
    open_claims: int  # not in approved/rejected/closed


class StatusDistributionItem(BaseModel):
    status: str
    count: int


class StatusDistributionResponse(BaseModel):
    items: list[StatusDistributionItem]
    total: int


class TimelinePoint(BaseModel):
    date: str  # ISO date (YYYY-MM-DD)
    count: int


class TimelineResponse(BaseModel):
    items: list[TimelinePoint]


class CoverageDistributionItem(BaseModel):
    coverage_type: str
    count: int


class CoverageDistributionResponse(BaseModel):
    items: list[CoverageDistributionItem]
    total: int


class AnalystProductivityItem(BaseModel):
    analyst_id: str
    analyst_name: str
    assigned: int
    decided: int


class AnalystProductivityResponse(BaseModel):
    items: list[AnalystProductivityItem]


class TopInconsistencyItem(BaseModel):
    field: str
    count: int


class AIKPIsResponse(BaseModel):
    """KPIs de IA — fase 2 de CU-21 (Ciclo 8)."""

    suspicious_claims: int  # fraud_score > umbral
    scored_claims: int  # claims con fraud_score calculado
    high_fraud_rate: float  # suspicious / scored
    fraud_alert_threshold: float
    total_inconsistency_findings: int
    top_inconsistencies: list[TopInconsistencyItem]
