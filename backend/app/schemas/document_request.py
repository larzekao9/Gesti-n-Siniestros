"""Document request Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentRequestCreate(BaseModel):
    description: str = Field(..., min_length=1, max_length=2000)


class DocumentRequestSubmit(BaseModel):
    evidence_ids: list[UUID] = Field(..., min_length=1)


class DocumentRequestOut(BaseModel):
    id: UUID
    tenant_id: UUID
    claim_id: UUID
    requested_by_user_id: UUID
    description: str
    status: str
    resolved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class DocumentRequestListResponse(BaseModel):
    items: list[DocumentRequestOut]
    total: int
    page: int
    limit: int
