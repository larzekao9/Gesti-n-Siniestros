"""Pydantic schemas for observations."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ObservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    claim_id: UUID
    author_user_id: UUID | None
    comment: str
    is_internal: bool
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime | None


class ObservationCreate(BaseModel):
    comment: str = Field(min_length=1, max_length=5000)
    is_internal: bool = False


class ObservationListResponse(BaseModel):
    items: list[ObservationOut]
    total: int
    page: int
    limit: int
