"""Tests for CU-21: operational dashboard analytics."""

from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim import Claim, ClaimDecision, ClaimSource, ClaimStatus
from app.models.claim_request import ClaimRequest, ClaimRequestStatus
from app.models.policy import Policy
from app.models.policyholder import Policyholder
from app.models.tenant import Tenant
from app.models.vehicle import Vehicle

HEADERS = {"X-Tenant-Slug": "aseguradora-a"}


async def _login(async_client: AsyncClient, email: str) -> str:
    resp = await async_client.post(
        "/api/auth/login",
        json={"email": email, "password": "Password123!"},
        headers=HEADERS,
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", **HEADERS}


async def _seed_chain(db: AsyncSession, tenant: Tenant, suffix: str, coverage: str = "full"):
    ph = Policyholder(
        tenant_id=tenant.id, document_id=f"DOC-{suffix}", full_name=f"PH {suffix}", phone="3000"
    )
    db.add(ph)
    await db.flush()
    pol = Policy(
        tenant_id=tenant.id,
        policy_number=f"POL-{suffix}",
        policyholder_id=ph.id,
        valid_from=date(2026, 1, 1),
        valid_to=date(2026, 12, 31),
        coverage_type=coverage,
    )
    db.add(pol)
    await db.flush()
    veh = Vehicle(
        tenant_id=tenant.id, plate=f"PL-{suffix}", make="Toyota", model="Corolla",
        year=2022, policy_id=pol.id,
    )
    db.add(veh)
    await db.flush()
    return ph, pol, veh


async def _seed_claim(
    db: AsyncSession,
    tenant: Tenant,
    suffix: str,
    *,
    status: ClaimStatus,
    coverage: str = "full",
    analyst_id=None,
    decided: bool = False,
    decision: ClaimDecision | None = None,
    created_days_ago: int = 5,
) -> Claim:
    ph, pol, veh = await _seed_chain(db, tenant, suffix, coverage)
    now = datetime.now(timezone.utc)
    claim = Claim(
        tenant_id=tenant.id,
        claim_number=f"EXP-{suffix}",
        policyholder_id=ph.id,
        policy_id=pol.id,
        vehicle_id=veh.id,
        status=status,
        source=ClaimSource.INTERNAL,
        accident_date=date(2026, 5, 1),
        accident_location="Calle 10",
        created_by_user_id=None,
        assigned_analyst_id=analyst_id,
        created_at=now - timedelta(days=created_days_ago),
    )
    if decided:
        claim.decision = decision
        claim.decided_at = now
    db.add(claim)
    await db.flush()
    return claim


@pytest.mark.asyncio
async def test_kpis_happy_path(async_client, db_session, tenant_a, user_admin, user_analyst):
    await _seed_claim(db_session, tenant_a, "A1", status=ClaimStatus.IN_REVIEW,
                      analyst_id=user_analyst.id)
    await _seed_claim(db_session, tenant_a, "A2", status=ClaimStatus.APPROVED,
                      analyst_id=user_analyst.id, decided=True,
                      decision=ClaimDecision.APPROVED, created_days_ago=10)
    await _seed_claim(db_session, tenant_a, "A3", status=ClaimStatus.REJECTED,
                      analyst_id=user_analyst.id, decided=True,
                      decision=ClaimDecision.REJECTED, created_days_ago=4)
    db_session.add(ClaimRequest(
        tenant_id=tenant_a.id, request_number="REQ-1",
        status=ClaimRequestStatus.REJECTED_AT_INTAKE,
        policyholder_id=uuid4(), policy_id=uuid4(), vehicle_id=uuid4(),
    ))
    await db_session.commit()

    token = await _login(async_client, "admin@aseguradora-a.com")
    resp = await async_client.get("/api/analytics/kpis", headers=_auth(token))
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total_claims"] == 3
    assert data["claims_by_status"]["in_review"] == 1
    assert data["claims_by_status"]["approved"] == 1
    assert data["open_claims"] == 1  # only in_review is open
    assert data["approval_rate"] == 0.5  # 1 approved / (1+1)
    assert data["total_requests"] == 1
    assert data["intake_rejection_rate"] == 1.0
    assert data["avg_days_to_decision"] is not None


@pytest.mark.asyncio
async def test_kpis_forbidden_for_analyst(async_client, db_session, tenant_a, user_analyst):
    await db_session.commit()
    token = await _login(async_client, "analyst@aseguradora-a.com")
    resp = await async_client.get("/api/analytics/kpis", headers=_auth(token))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_status_and_coverage_distribution(async_client, db_session, tenant_a, user_admin):
    await _seed_claim(db_session, tenant_a, "S1", status=ClaimStatus.IN_REVIEW, coverage="full")
    await _seed_claim(db_session, tenant_a, "S2", status=ClaimStatus.IN_REVIEW, coverage="basic")
    await _seed_claim(db_session, tenant_a, "S3", status=ClaimStatus.CLOSED, coverage="full")
    await db_session.commit()

    token = await _login(async_client, "admin@aseguradora-a.com")

    sd = await async_client.get("/api/analytics/status-distribution", headers=_auth(token))
    assert sd.status_code == 200
    by = {i["status"]: i["count"] for i in sd.json()["items"]}
    assert by["in_review"] == 2 and by["closed"] == 1
    assert sd.json()["total"] == 3

    cd = await async_client.get("/api/analytics/coverage-distribution", headers=_auth(token))
    assert cd.status_code == 200
    cov = {i["coverage_type"]: i["count"] for i in cd.json()["items"]}
    assert cov["full"] == 2 and cov["basic"] == 1


@pytest.mark.asyncio
async def test_timeline_and_productivity(async_client, db_session, tenant_a, user_admin, user_analyst):
    await _seed_claim(db_session, tenant_a, "T1", status=ClaimStatus.APPROVED,
                      analyst_id=user_analyst.id, decided=True, decision=ClaimDecision.APPROVED)
    await _seed_claim(db_session, tenant_a, "T2", status=ClaimStatus.IN_REVIEW,
                      analyst_id=user_analyst.id)
    await db_session.commit()

    token = await _login(async_client, "admin@aseguradora-a.com")

    tl = await async_client.get("/api/analytics/timeline", headers=_auth(token))
    assert tl.status_code == 200
    assert sum(p["count"] for p in tl.json()["items"]) == 2

    pr = await async_client.get("/api/analytics/analyst-productivity", headers=_auth(token))
    assert pr.status_code == 200
    items = pr.json()["items"]
    assert len(items) == 1
    assert items[0]["assigned"] == 2 and items[0]["decided"] == 1


@pytest.mark.asyncio
async def test_multitenant_isolation(async_client, db_session, tenant_a, tenant_b, user_admin):
    # Claim en tenant B no debe contar para admin de tenant A.
    await _seed_claim(db_session, tenant_b, "B1", status=ClaimStatus.IN_REVIEW)
    await _seed_claim(db_session, tenant_a, "A1", status=ClaimStatus.IN_REVIEW)
    await db_session.commit()

    token = await _login(async_client, "admin@aseguradora-a.com")
    resp = await async_client.get("/api/analytics/kpis", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["total_claims"] == 1
