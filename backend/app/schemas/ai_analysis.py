"""Pydantic schemas for AI analyses (CU-32 / CU-33)."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AIAnalysisOut(BaseModel):
    # protected_namespaces=(): permite el campo `model_version` sin warning.
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: UUID
    claim_id: UUID | None
    claim_request_id: UUID | None
    evidence_id: UUID | None
    kind: str
    status: str
    score: Decimal | None
    payload: dict | None
    explanation: str | None
    model_version: str | None
    created_at: datetime
    updated_at: datetime | None


class AIAnalysisListResponse(BaseModel):
    items: list[AIAnalysisOut]


class AIRefreshResponse(BaseModel):
    detail: str
    enqueued: bool
