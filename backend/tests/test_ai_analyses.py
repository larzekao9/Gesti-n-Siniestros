"""Tests del Ciclo 8 — Análisis Inteligente (CU-32 / CU-33).

Mocks de OpenAI en todos los caminos que tocan la API (no consume cuota).
El fraude heurístico (ADR-010) se testea puro, sin mocks. La detección de
duplicados se testea con el fallback Python (SQLite degrada vector→JSON).
"""

import json
from datetime import date, datetime, time, timedelta
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient

from app.models.ai_analysis import (
    AIAnalysis,
    AIAnalysisKind,
    AIAnalysisStatus,
    ClaimEmbedding,
)
from app.models.claim import Claim
from app.models.evidence import Evidence, EvidenceType
from app.models.policy import Policy
from app.services.ai.claim_context import ClaimContext
from app.services.ai.fraud_score_service import fraud_score_service

TENANT = "aseguradora-a"


def _h(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "X-Tenant-Slug": TENANT}


async def _login(async_client: AsyncClient, email: str = "admin@aseguradora-a.com") -> str:
    resp = await async_client.post(
        "/api/auth/login",
        json={"email": email, "password": "Password123!"},
        headers={"X-Tenant-Slug": TENANT},
    )
    return resp.json()["access_token"]


async def _make_claim(async_client: AsyncClient, token: str, suffix: str) -> str:
    today = date.today()
    ph = await async_client.post(
        "/api/policyholders",
        json={"document_id": f"DOC-AI-{suffix}", "full_name": f"Holder {suffix}", "phone": "70000000"},
        headers=_h(token),
    )
    ph_id = ph.json()["id"]
    pol = await async_client.post(
        "/api/policies",
        json={
            "policy_number": f"POL-AI-{suffix}",
            "policyholder_id": ph_id,
            "valid_from": str(today - timedelta(days=10)),
            "valid_to": str(today + timedelta(days=355)),
            "coverage_type": "full",
        },
        headers=_h(token),
    )
    pol_id = pol.json()["id"]
    veh = await async_client.post(
        "/api/vehicles",
        json={
            "plate": f"AI-{suffix}",
            "make": "Toyota",
            "model": "Corolla",
            "year": 2022,
            "vehicle_type": "sedan",
            "policy_id": pol_id,
        },
        headers=_h(token),
    )
    resp = await async_client.post(
        "/api/claims",
        json={
            "policyholder_id": ph_id,
            "policy_id": pol_id,
            "vehicle_id": veh.json()["id"],
            "accident_date": str(today),
            "accident_location": "Av. Test 123",
            "accident_description": "Choque trasero leve",
        },
        headers=_h(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _ctx(*, claim=None, policy=None, evidences=None, prior=0) -> ClaimContext:
    """ClaimContext con instancias en memoria (sin BD) para tests puros."""
    today = date.today()
    if claim is None:
        claim = Claim(
            tenant_id=uuid4(),
            claim_number="EXP-T",
            policyholder_id=uuid4(),
            policy_id=uuid4(),
            vehicle_id=uuid4(),
            accident_date=today,
            accident_location="x",
        )
        claim.created_at = datetime.now()
    return ClaimContext(
        claim=claim,
        policyholder=None,
        policy=policy,
        vehicle=None,
        evidences=evidences or [],
        prior_claims_count=prior,
    )


# ─── FraudScoreService (heurístico puro, ADR-010) ───────────────────


def test_fraud_score_high_risk_factors():
    today = date.today()
    claim = Claim(
        tenant_id=uuid4(),
        claim_number="EXP-HI",
        policyholder_id=uuid4(),
        policy_id=uuid4(),
        vehicle_id=uuid4(),
        accident_date=today,
        accident_time=time(3, 30),  # nocturno
        accident_location="x",
    )
    claim.created_at = datetime.now()
    policy = Policy(
        tenant_id=claim.tenant_id,
        policy_number="P",
        policyholder_id=claim.policyholder_id,
        valid_from=today - timedelta(days=5),  # póliza nueva
        valid_to=today + timedelta(days=360),
        coverage_type="full",
    )
    result = fraud_score_service.compute(
        ctx=_ctx(claim=claim, policy=policy, evidences=[], prior=3),
        duplicate_top_similarity=0.95,
    )
    assert result["score"] > 0.8
    names = [f["name"] for f in result["payload"]["factors"]]
    assert any("nocturno" in n for n in names)
    assert any("30 días" in n for n in names)
    assert any("duplicado" in n for n in names)
    assert all(f["direction"] in ("up", "down") for f in result["payload"]["factors"])
    assert "Aumentan el riesgo" in result["explanation"]


def test_fraud_score_low_risk_with_mitigators():
    today = date.today()
    claim = Claim(
        tenant_id=uuid4(),
        claim_number="EXP-LO",
        policyholder_id=uuid4(),
        policy_id=uuid4(),
        vehicle_id=uuid4(),
        accident_date=today,
        accident_time=time(14, 0),
        accident_location="x",
        accident_lat=1.0,
        accident_lng=2.0,
    )
    claim.created_at = datetime.now()
    policy = Policy(
        tenant_id=claim.tenant_id,
        policy_number="P",
        policyholder_id=claim.policyholder_id,
        valid_from=today - timedelta(days=900),  # 2+ años
        valid_to=today + timedelta(days=100),
        coverage_type="full",
    )
    police_report = Evidence(
        tenant_id=claim.tenant_id,
        claim_id=claim.id,
        type=EvidenceType.POLICE_REPORT,
        file_url="k",
        file_name="acta.pdf",
        mime_type="application/pdf",
        file_size=10,
    )
    result = fraud_score_service.compute(
        ctx=_ctx(claim=claim, policy=policy, evidences=[police_report], prior=0)
    )
    assert result["score"] < 0.2
    directions = {f["direction"] for f in result["payload"]["factors"]}
    assert "down" in directions


def test_fraud_score_clamped_between_0_and_1():
    result = fraud_score_service.compute(ctx=_ctx(prior=5))
    assert 0.0 <= result["score"] <= 1.0


# ─── DuplicateDetectionService (fallback Python en SQLite) ──────────


@pytest.mark.asyncio
async def test_duplicate_detection_flags_similar_claims(async_client, db_session, user_admin):
    token = await _login(async_client)
    claim_a = await _make_claim(async_client, token, "DUP-A")
    claim_b = await _make_claim(async_client, token, "DUP-B")

    claim_a_obj = await db_session.get(Claim, UUID(claim_a))
    vec = [1.0, 0.0, 0.5, 0.2]
    db_session.add(
        ClaimEmbedding(
            tenant_id=claim_a_obj.tenant_id,
            claim_id=UUID(claim_b),
            embedding=[1.0, 0.0, 0.5, 0.21],  # casi idéntico → similitud ~1
            source_text_hash="h",
        )
    )
    await db_session.commit()

    from app.services.ai.duplicate_service import duplicate_service

    ctx = _ctx(claim=claim_a_obj)
    result = await duplicate_service.analyze(db_session, ctx=ctx, embedding=vec)
    assert result["score"] is not None and result["score"] >= 0.99
    matches = result["payload"]["matches"]
    assert len(matches) == 1
    assert matches[0]["claim_id"] == claim_b
    assert matches[0]["claim_number"].startswith("EXP-")


@pytest.mark.asyncio
async def test_duplicate_detection_no_matches_below_threshold(async_client, db_session, user_admin):
    token = await _login(async_client)
    claim_a = await _make_claim(async_client, token, "DUP-C")
    claim_b = await _make_claim(async_client, token, "DUP-D")
    claim_a_obj = await db_session.get(Claim, UUID(claim_a))
    db_session.add(
        ClaimEmbedding(
            tenant_id=claim_a_obj.tenant_id,
            claim_id=UUID(claim_b),
            embedding=[0.0, 1.0, 0.0, 0.0],  # ortogonal → similitud ~0
            source_text_hash="h",
        )
    )
    await db_session.commit()

    from app.services.ai.duplicate_service import duplicate_service

    result = await duplicate_service.analyze(
        db_session, ctx=_ctx(claim=claim_a_obj), embedding=[1.0, 0.0, 0.0, 0.0]
    )
    assert result["payload"]["matches"] == []


# ─── InconsistencyAnalysisService (mock OpenAI) ─────────────────────


class _FakeChatClient:
    """Stub de AsyncOpenAI: devuelve el JSON configurado."""

    def __init__(self, content: dict):
        async def _create(**kwargs):
            message = SimpleNamespace(content=json.dumps(content))
            return SimpleNamespace(choices=[SimpleNamespace(message=message)])

        self.chat = SimpleNamespace(completions=SimpleNamespace(create=_create))


@pytest.mark.asyncio
async def test_inconsistency_analysis_parses_findings(async_client, db_session, user_admin, monkeypatch):
    token = await _login(async_client)
    claim_id = await _make_claim(async_client, token, "INC")
    claim = await db_session.get(Claim, UUID(claim_id))

    fake = _FakeChatClient(
        {
            "findings": [
                {"severity": "critical", "field": "accident_date", "message": "Fecha fuera de vigencia"},
                {"severity": "inventada", "field": "x", "message": "severidad inválida → degrada a info"},
            ]
        }
    )
    monkeypatch.setattr(
        "app.services.ai.inconsistency_service.get_openai_client", lambda: fake
    )

    from app.services.ai.inconsistency_service import inconsistency_service

    result = await inconsistency_service.analyze(db_session, ctx=_ctx(claim=claim))
    findings = result["payload"]["findings"]
    assert len(findings) == 2
    assert findings[0]["severity"] == "critical"
    assert findings[1]["severity"] == "info"  # sanitizada
    assert "1 crítica" in result["explanation"]


# ─── CU-32: endpoints ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_ai_analyses_returns_latest_per_kind(async_client, db_session, user_admin):
    token = await _login(async_client)
    claim_id = await _make_claim(async_client, token, "GET")
    claim = await db_session.get(Claim, UUID(claim_id))

    old = AIAnalysis(
        tenant_id=claim.tenant_id,
        claim_id=claim.id,
        kind=AIAnalysisKind.FRAUD_SCORE,
        status=AIAnalysisStatus.DONE,
        payload={"score": 0.1, "factors": []},
    )
    old.created_at = datetime.now() - timedelta(hours=1)
    new = AIAnalysis(
        tenant_id=claim.tenant_id,
        claim_id=claim.id,
        kind=AIAnalysisKind.FRAUD_SCORE,
        status=AIAnalysisStatus.DONE,
        payload={"score": 0.9, "factors": []},
    )
    new.created_at = datetime.now()
    inc = AIAnalysis(
        tenant_id=claim.tenant_id,
        claim_id=claim.id,
        kind=AIAnalysisKind.INCONSISTENCY,
        status=AIAnalysisStatus.PROCESSING,
    )
    db_session.add_all([old, new, inc])
    await db_session.commit()

    resp = await async_client.get(f"/api/claims/{claim_id}/ai-analyses", headers=_h(token))
    assert resp.status_code == 200
    items = resp.json()["items"]
    kinds = {i["kind"]: i for i in items}
    assert len(items) == 2  # 1 por kind (el más reciente)
    assert kinds["fraud_score"]["payload"]["score"] == 0.9
    assert kinds["inconsistency"]["status"] == "processing"


@pytest.mark.asyncio
async def test_get_ai_analyses_unknown_claim_404(async_client, user_admin):
    token = await _login(async_client)
    resp = await async_client.get(f"/api/claims/{uuid4()}/ai-analyses", headers=_h(token))
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_refresh_requires_supervisor_or_admin(async_client, user_admin, user_analyst):
    admin_token = await _login(async_client)
    claim_id = await _make_claim(async_client, admin_token, "REF-403")
    analyst_token = await _login(async_client, "analyst@aseguradora-a.com")
    resp = await async_client.post(
        f"/api/claims/{claim_id}/ai-analyses/refresh", headers=_h(analyst_token)
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_refresh_enqueues_task(async_client, user_admin, monkeypatch):
    calls = []
    from app.tasks.ai_analysis import run_claim_ai_analysis

    monkeypatch.setattr(
        run_claim_ai_analysis, "apply_async", lambda *a, **kw: calls.append(kw)
    )
    token = await _login(async_client)
    claim_id = await _make_claim(async_client, token, "REF-OK")
    resp = await async_client.post(
        f"/api/claims/{claim_id}/ai-analyses/refresh", headers=_h(token)
    )
    assert resp.status_code == 202
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_status_change_to_in_evaluation_triggers_analysis(async_client, user_admin, monkeypatch):
    calls = []
    from app.tasks.ai_analysis import run_claim_ai_analysis

    monkeypatch.setattr(
        run_claim_ai_analysis, "apply_async", lambda *a, **kw: calls.append(kw)
    )
    token = await _login(async_client)
    claim_id = await _make_claim(async_client, token, "TRIG")

    r1 = await async_client.patch(
        f"/api/claims/{claim_id}/status",
        json={"new_status": "in_review"},
        headers=_h(token),
    )
    assert r1.status_code == 200, r1.text
    assert len(calls) == 0  # in_review NO dispara

    r2 = await async_client.patch(
        f"/api/claims/{claim_id}/status",
        json={"new_status": "in_evaluation"},
        headers=_h(token),
    )
    assert r2.status_code == 200, r2.text
    assert len(calls) == 1  # in_evaluation SÍ dispara


# ─── CU-33: análisis de daño por foto (canal asegurado) ─────────────


async def _insured_with_draft_and_photo(async_client: AsyncClient) -> dict:
    """Cuenta asegurada + draft + evidencia foto. Reusa el flujo del Ciclo 7."""
    today = date.today()
    admin = await _login(async_client)
    ph = await async_client.post(
        "/api/policyholders",
        json={"document_id": "DOC-CU33", "full_name": "Asegurado CU33", "phone": "70000000", "email": "cu33@mail.com"},
        headers=_h(admin),
    )
    ph_id = ph.json()["id"]
    pol = await async_client.post(
        "/api/policies",
        json={
            "policy_number": "POL-CU33",
            "policyholder_id": ph_id,
            "valid_from": str(today),
            "valid_to": str(today + timedelta(days=365)),
            "coverage_type": "full",
        },
        headers=_h(admin),
    )
    veh = await async_client.post(
        "/api/vehicles",
        json={"plate": "CU33", "make": "Kia", "model": "Rio", "year": 2021, "vehicle_type": "sedan", "policy_id": pol.json()["id"]},
        headers=_h(admin),
    )
    inv = await async_client.post(f"/api/policyholders/{ph_id}/invite", headers=_h(admin))
    reg = await async_client.post(
        "/api/insured-auth/register",
        json={"activation_token": inv.json()["activation_token"], "password": "Insured123!"},
    )
    insured_token = reg.json()["access_token"]

    draft = await async_client.post(
        "/api/me/claim-requests",
        json={
            "policyholder_id": ph_id,
            "policy_id": pol.json()["id"],
            "vehicle_id": veh.json()["id"],
            "accident_date": str(today),
            "accident_location": "Calle 1",
        },
        headers=_h(insured_token),
    )
    req_id = draft.json()["id"]
    ev = await async_client.post(
        f"/api/me/claim-requests/{req_id}/evidences",
        json={
            "s3_key": "claim_request/x/foto.jpg",
            "type": "photo",
            "file_name": "foto.jpg",
            "mime_type": "image/jpeg",
            "file_size": 2048,
        },
        headers=_h(insured_token),
    )
    return {"token": insured_token, "request_id": req_id, "evidence_id": ev.json()["id"]}


@pytest.mark.asyncio
async def test_analyze_damage_happy_path(async_client, user_admin, monkeypatch):
    setup = await _insured_with_draft_and_photo(async_client)

    fake = _FakeChatClient(
        {
            "damage_type": "colisión trasera",
            "severity": "moderado",
            "confidence": 0.87,
            "explanation": "Paragolpes trasero hundido y faro roto.",
        }
    )
    monkeypatch.setattr(
        "app.services.ai.damage_vision_service.get_openai_client", lambda: fake
    )
    monkeypatch.setattr(
        "app.services.storage_service.storage_service.get_object_bytes",
        lambda key: b"\xff\xd8fakejpeg",
    )

    resp = await async_client.post(
        f"/api/me/claim-requests/{setup['request_id']}/evidences/{setup['evidence_id']}/analyze-damage",
        headers=_h(setup["token"]),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["kind"] == "damage_assessment"
    assert data["status"] == "done"
    assert data["payload"]["damage_type"] == "colisión trasera"
    assert data["payload"]["severity"] == "moderado"
    assert data["claim_request_id"] == setup["request_id"]


@pytest.mark.asyncio
async def test_analyze_damage_vision_failure_returns_error_status(async_client, user_admin, monkeypatch):
    setup = await _insured_with_draft_and_photo(async_client)

    def _boom(key):
        raise RuntimeError("S3 caído")

    monkeypatch.setattr(
        "app.services.storage_service.storage_service.get_object_bytes", _boom
    )

    resp = await async_client.post(
        f"/api/me/claim-requests/{setup['request_id']}/evidences/{setup['evidence_id']}/analyze-damage",
        headers=_h(setup["token"]),
    )
    # F-A1: el análisis falla pero el endpoint responde con status=error
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "error"


@pytest.mark.asyncio
async def test_analyze_damage_unknown_evidence_404(async_client, user_admin):
    setup = await _insured_with_draft_and_photo(async_client)
    resp = await async_client.post(
        f"/api/me/claim-requests/{setup['request_id']}/evidences/{uuid4()}/analyze-damage",
        headers=_h(setup["token"]),
    )
    assert resp.status_code == 404
