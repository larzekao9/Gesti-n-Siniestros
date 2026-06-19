"""Tests for CU-22: operational report generation (PDF / Excel)."""

from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.claim import Claim, ClaimSource, ClaimStatus
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


async def _seed_claim(db: AsyncSession, tenant: Tenant, suffix: str) -> Claim:
    ph = Policyholder(tenant_id=tenant.id, document_id=f"DOC-{suffix}",
                      full_name=f"PH {suffix}", phone="3000")
    db.add(ph)
    await db.flush()
    pol = Policy(tenant_id=tenant.id, policy_number=f"POL-{suffix}", policyholder_id=ph.id,
                 valid_from=date(2026, 1, 1), valid_to=date(2026, 12, 31), coverage_type="full")
    db.add(pol)
    await db.flush()
    veh = Vehicle(tenant_id=tenant.id, plate=f"PL-{suffix}", make="Toyota", model="Corolla",
                  year=2022, policy_id=pol.id)
    db.add(veh)
    await db.flush()
    claim = Claim(
        tenant_id=tenant.id, claim_number=f"EXP-{suffix}", policyholder_id=ph.id,
        policy_id=pol.id, vehicle_id=veh.id, status=ClaimStatus.IN_REVIEW,
        source=ClaimSource.INTERNAL, accident_date=date(2026, 5, 1),
        accident_location="Calle 10", created_by_user_id=None,
    )
    db.add(claim)
    await db.flush()
    return claim


@pytest.mark.asyncio
async def test_pdf_report_happy_path(async_client, db_session, tenant_a, user_admin):
    await _seed_claim(db_session, tenant_a, "R1")
    await db_session.commit()

    token = await _login(async_client, "admin@aseguradora-a.com")
    resp = await async_client.get("/api/reports/claims?format=pdf", headers=_auth(token))
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content[:4] == b"%PDF"
    assert "attachment" in resp.headers["content-disposition"]

    # CU-22 postcondición: la generación queda auditada.
    logs = (await db_session.execute(
        select(AuditLog).where(AuditLog.action == "REPORT_GENERATE")
    )).scalars().all()
    assert len(logs) == 1
    assert logs[0].payload_diff["format"] == "pdf"


@pytest.mark.asyncio
async def test_xlsx_report_happy_path(async_client, db_session, tenant_a, user_admin):
    await _seed_claim(db_session, tenant_a, "R2")
    await db_session.commit()

    token = await _login(async_client, "admin@aseguradora-a.com")
    resp = await async_client.get("/api/reports/claims?format=xlsx", headers=_auth(token))
    assert resp.status_code == 200, resp.text
    assert "spreadsheetml" in resp.headers["content-type"]
    # XLSX = zip container → starts with PK.
    assert resp.content[:2] == b"PK"


@pytest.mark.asyncio
async def test_empty_report_returns_200(async_client, db_session, tenant_a, user_admin):
    await db_session.commit()
    token = await _login(async_client, "admin@aseguradora-a.com")
    resp = await async_client.get("/api/reports/claims?format=pdf", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.content[:4] == b"%PDF"


@pytest.mark.asyncio
async def test_report_forbidden_for_analyst(async_client, db_session, tenant_a, user_analyst):
    await db_session.commit()
    token = await _login(async_client, "analyst@aseguradora-a.com")
    resp = await async_client.get("/api/reports/claims?format=pdf", headers=_auth(token))
    assert resp.status_code == 403
