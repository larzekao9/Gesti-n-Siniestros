"""Pydantic schemas for policy CRUD."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PolicyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    policy_number: str
    policyholder_id: UUID
    valid_from: date
    valid_to: date
    coverage_type: str
    exclusions: str | None
    status: str
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime | None


class PolicyCreate(BaseModel):
    policy_number: str = Field(min_length=3, max_length=50)
    policyholder_id: UUID
    valid_from: date
    valid_to: date
    coverage_type: str = Field(min_length=2, max_length=100)
    exclusions: str | None = None

    @model_validator(mode="after")
    def dates_coherent(self) -> "PolicyCreate":
        if self.valid_from >= self.valid_to:
            raise ValueError("valid_from debe ser anterior a valid_to")
        return self


class PolicyUpdate(BaseModel):
    policy_number: str | None = Field(default=None, min_length=3, max_length=50)
    valid_from: date | None = None
    valid_to: date | None = None
    coverage_type: str | None = None
    exclusions: str | None = None
    status: str | None = None


class PolicyListResponse(BaseModel):
    items: list[PolicyOut]
    total: int
    page: int
    limit: int
