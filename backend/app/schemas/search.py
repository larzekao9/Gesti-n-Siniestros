"""Reusable search/filter schemas for CU-30."""

from datetime import date

from pydantic import BaseModel


class ClaimSearchParams(BaseModel):
    q: str | None = None
    status: str | None = None
    from_date: date | None = None
    to_date: date | None = None
    analyst_id: str | None = None
    policyholder_id: str | None = None
    page: int = 1
    limit: int = 20


class ClaimRequestSearchParams(BaseModel):
    q: str | None = None
    status: str | None = None
    from_date: date | None = None
    to_date: date | None = None
    page: int = 1
    limit: int = 20
