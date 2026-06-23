"""Tests for CU-22 (PDF / Excel) y CU-37 (reportes por voz)."""

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
from app.models.user import Role, User
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


# ─── CU-37: reportes por voz (interpretación, mock del LLM) ──────────


def _mock_intent(monkeypatch, intent: dict) -> None:
    """Reemplaza el paso LLM por una intención fija (sin tocar OpenAI)."""
    from app.services.ai.report_voice_service import report_voice_service

    async def _fake(_text: str) -> dict:
        return intent

    monkeypatch.setattr(report_voice_service, "_llm_intent", _fake)


@pytest.mark.asyncio
async def test_interpret_maps_status_and_format(async_client, db_session, tenant_a, user_admin, monkeypatch):
    await db_session.commit()
    _mock_intent(monkeypatch, {
        "supported": True, "format": "xlsx", "status": "approved",
        "date_from": "2026-06-01", "date_to": "2026-06-30",
        "analyst_name": None, "supervisor_name": None, "policyholder_name": None,
        "q": None, "note": "",
    })
    token = await _login(async_client, "admin@aseguradora-a.com")
    resp = await async_client.post(
        "/api/reports/interpret",
        json={"text": "dame en excel los aprobados de junio"},
        headers=_auth(token),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["supported"] is True
    assert body["filters"]["format"] == "xlsx"
    assert body["filters"]["status"] == "approved"
    assert body["filters"]["from"] == "2026-06-01"
    assert body["resolved"]["status_label"] == "Aprobado"


@pytest.mark.asyncio
async def test_interpret_resolves_analyst_name(async_client, db_session, tenant_a, user_admin, monkeypatch):
    analyst = User(
        tenant_id=tenant_a.id, email="jperez@aseguradora-a.com",
        hashed_password="x", full_name="Juan Pérez", role=Role.ANALYST, is_active=True,
    )
    db_session.add(analyst)
    await db_session.commit()

    _mock_intent(monkeypatch, {
        "supported": True, "format": "pdf", "status": None,
        "date_from": None, "date_to": None,
        "analyst_name": "juan perez", "supervisor_name": None,
        "policyholder_name": None, "q": None, "note": "",
    })
    token = await _login(async_client, "admin@aseguradora-a.com")
    resp = await async_client.post(
        "/api/reports/interpret",
        json={"text": "los del analista juan perez"},
        headers=_auth(token),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["filters"]["analyst"] == str(analyst.id)
    assert body["resolved"]["analyst_label"] == "Juan Pérez"
    assert body["warnings"] == []


@pytest.mark.asyncio
async def test_interpret_warns_on_unknown_analyst(async_client, db_session, tenant_a, user_admin, monkeypatch):
    await db_session.commit()
    _mock_intent(monkeypatch, {
        "supported": True, "format": "pdf", "status": None,
        "date_from": None, "date_to": None,
        "analyst_name": "Nadie Existe", "supervisor_name": None,
        "policyholder_name": None, "q": None, "note": "",
    })
    token = await _login(async_client, "admin@aseguradora-a.com")
    resp = await async_client.post(
        "/api/reports/interpret",
        json={"text": "los del analista nadie existe"},
        headers=_auth(token),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["filters"]["analyst"] is None
    assert any("Nadie Existe" in w for w in body["warnings"])


@pytest.mark.asyncio
async def test_interpret_unsupported_request(async_client, db_session, tenant_a, user_admin, monkeypatch):
    await db_session.commit()
    _mock_intent(monkeypatch, {
        "supported": False, "format": None, "status": None,
        "date_from": None, "date_to": None, "analyst_name": None,
        "supervisor_name": None, "policyholder_name": None, "q": None,
        "note": "Ese reporte no está disponible.",
    })
    token = await _login(async_client, "admin@aseguradora-a.com")
    resp = await async_client.post(
        "/api/reports/interpret",
        json={"text": "ranking de productividad de analistas"},
        headers=_auth(token),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["supported"] is False
    assert "no está disponible" in body["note"]


@pytest.mark.asyncio
async def test_interpret_forbidden_for_analyst(async_client, db_session, tenant_a, user_analyst):
    await db_session.commit()
    token = await _login(async_client, "analyst@aseguradora-a.com")
    resp = await async_client.post(
        "/api/reports/interpret",
        json={"text": "dame los aprobados"},
        headers=_auth(token),
    )
    assert resp.status_code == 403
