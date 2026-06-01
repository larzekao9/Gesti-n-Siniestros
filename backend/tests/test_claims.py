"""Tests for Cycle 3: Claims, Claim Requests, Observations, Third Parties."""

import asyncio
import pytest
from httpx import AsyncClient
from datetime import date, timedelta
from uuid import UUID

from app.models.claim_request import ClaimRequest, ClaimRequestStatus


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "X-Tenant-Slug": "aseguradora-a"}


async def _login(async_client: AsyncClient) -> str:
    resp = await async_client.post(
        "/api/auth/login",
        json={"email": "admin@aseguradora-a.com", "password": "Password123!"},
        headers={"X-Tenant-Slug": "aseguradora-a"},
    )
    return resp.json()["access_token"]


async def _create_policyholder(async_client: AsyncClient, token: str, suffix: str = "") -> str:
    key = f"PH-TEST-{suffix}"
    resp = await async_client.post(
        "/api/policyholders",
        json={"document_id": key, "full_name": f"Test Holder {suffix}", "phone": "3000000"},
        headers=_headers(token),
    )
    return resp.json()["id"]


async def _create_policy(async_client: AsyncClient, token: str, ph_id: str, suffix: str = "") -> str:
    today = date.today()
    resp = await async_client.post(
        "/api/policies",
        json={
            "policy_number": f"POL-TEST-{suffix}",
            "policyholder_id": ph_id,
            "valid_from": str(today),
            "valid_to": str(today + timedelta(days=365)),
            "coverage_type": "full",
        },
        headers=_headers(token),
    )
    return resp.json()["id"]


async def _create_vehicle(async_client: AsyncClient, token: str, policy_id: str, suffix: str = "") -> str:
    resp = await async_client.post(
        "/api/vehicles",
        json={
            "plate": f"PLATE-{suffix}",
            "make": "Toyota",
            "model": "Corolla",
            "year": 2022,
            "vehicle_type": "sedan",
            "policy_id": policy_id,
        },
        headers=_headers(token),
    )
    return resp.json()["id"]


# ─── Claims ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_claim_internal_success(async_client, user_admin):
    token = await _login(async_client)
    ph_id = await _create_policyholder(async_client, token, "CL-IS")
    pol_id = await _create_policy(async_client, token, ph_id, "CL-IS")
    veh_id = await _create_vehicle(async_client, token, pol_id, "CL-IS")

    resp = await async_client.post(
        "/api/claims",
        json={
            "policyholder_id": ph_id,
            "policy_id": pol_id,
            "vehicle_id": veh_id,
            "accident_date": str(date.today()),
            "accident_location": "Av. Siempre Viva 742",
        },
        headers=_headers(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["claim_number"].startswith("EXP-")
    assert data["status"] == "registered"


@pytest.mark.asyncio
async def test_create_claim_invalid_policy(async_client, user_admin):
    token = await _login(async_client)
    ph_id = await _create_policyholder(async_client, token, "CL-IVP")
    today = date.today()

    resp = await async_client.post(
        "/api/policies",
        json={
            "policy_number": "POL-FUTURE",
            "policyholder_id": ph_id,
            "valid_from": str(today + timedelta(days=30)),
            "valid_to": str(today + timedelta(days=365)),
            "coverage_type": "full",
        },
        headers=_headers(token),
    )
    pol_id = resp.json()["id"]
    veh_id = await _create_vehicle(async_client, token, pol_id, "CL-IVP")

    resp = await async_client.post(
        "/api/claims",
        json={
            "policyholder_id": ph_id,
            "policy_id": pol_id,
            "vehicle_id": veh_id,
            "accident_date": str(today),
            "accident_location": "Calle Falsa 123",
        },
        headers=_headers(token),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_claims(async_client, user_admin):
    token = await _login(async_client)
    ph_id = await _create_policyholder(async_client, token, "CL-LS")
    pol_id = await _create_policy(async_client, token, ph_id, "CL-LS")
    veh_id = await _create_vehicle(async_client, token, pol_id, "CL-LS")

    await async_client.post(
        "/api/claims",
        json={
            "policyholder_id": ph_id,
            "policy_id": pol_id,
            "vehicle_id": veh_id,
            "accident_date": str(date.today()),
            "accident_location": "Zona Norte",
        },
        headers=_headers(token),
    )

    resp = await async_client.get("/api/claims", headers=_headers(token))
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_search_claims(async_client, user_admin):
    token = await _login(async_client)
    ph_id = await _create_policyholder(async_client, token, "CL-SR")
    pol_id = await _create_policy(async_client, token, ph_id, "CL-SR")
    veh_id = await _create_vehicle(async_client, token, pol_id, "CL-SR")

    await async_client.post(
        "/api/claims",
        json={
            "policyholder_id": ph_id,
            "policy_id": pol_id,
            "vehicle_id": veh_id,
            "accident_date": str(date.today()),
            "accident_location": "Colisión en Rotonda Central",
        },
        headers=_headers(token),
    )

    resp = await async_client.get("/api/claims?q=Colisión", headers=_headers(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1

    resp_empty = await async_client.get("/api/claims?q=NOEXISTENTEZZZ", headers=_headers(token))
    assert resp_empty.status_code == 200
    assert resp_empty.json()["total"] == 0


# ─── Formalize flow ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_formalize_request_flow(async_client, db_session, user_admin):
    token = await _login(async_client)
    ph_id = await _create_policyholder(async_client, token, "CL-FR")
    pol_id = await _create_policy(async_client, token, ph_id, "CL-FR")
    veh_id = await _create_vehicle(async_client, token, pol_id, "CL-FR")

    today = date.today()
    cr = ClaimRequest(
        tenant_id=user_admin.tenant_id,
        status=ClaimRequestStatus.SUBMITTED,
        request_number="REQ-TEST-FORMALIZE",
        policyholder_id=UUID(ph_id),
        policy_id=UUID(pol_id),
        vehicle_id=UUID(veh_id),
        accident_date=today,
        accident_location="Intersección Central",
    )
    db_session.add(cr)
    await db_session.commit()
    req_id = str(cr.id)

    resp = await async_client.post(
        f"/api/claim-requests/{req_id}/take",
        headers=_headers(token),
    )
    assert resp.status_code == 200

    resp = await async_client.post(
        f"/api/claim-requests/{req_id}/formalize",
        headers=_headers(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "claim" in data
    assert "request" in data
    assert data["claim"]["status"] == "registered"
    assert data["request"]["status"] == "formalized"
    assert data["request"]["formalized_claim_id"] == data["claim"]["id"]


# ─── Intake operations ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_take_already_taken(async_client, db_session, user_admin):
    token = await _login(async_client)
    ph_id = await _create_policyholder(async_client, token, "CL-TAT")
    pol_id = await _create_policy(async_client, token, ph_id, "CL-TAT")
    veh_id = await _create_vehicle(async_client, token, pol_id, "CL-TAT")

    cr = ClaimRequest(
        tenant_id=user_admin.tenant_id,
        status=ClaimRequestStatus.SUBMITTED,
        request_number="REQ-TAKE-TWICE",
        policyholder_id=UUID(ph_id),
        policy_id=UUID(pol_id),
        vehicle_id=UUID(veh_id),
        accident_date=date.today(),
        accident_location="Lugar del hecho",
    )
    db_session.add(cr)
    await db_session.commit()
    req_id = str(cr.id)

    resp = await async_client.post(
        f"/api/claim-requests/{req_id}/take",
        headers=_headers(token),
    )
    assert resp.status_code == 200

    resp = await async_client.post(
        f"/api/claim-requests/{req_id}/take",
        headers=_headers(token),
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_take_concurrent_only_one_wins(async_client, db_session, user_admin):
    """CU-24: dos analistas piden take en paralelo, solo uno gana (409 para el otro)."""
    token = await _login(async_client)
    ph_id = await _create_policyholder(async_client, token, "CL-CONC")
    pol_id = await _create_policy(async_client, token, ph_id, "CL-CONC")
    veh_id = await _create_vehicle(async_client, token, pol_id, "CL-CONC")

    cr = ClaimRequest(
        tenant_id=user_admin.tenant_id,
        status=ClaimRequestStatus.SUBMITTED,
        request_number="REQ-RACE",
        policyholder_id=UUID(ph_id),
        policy_id=UUID(pol_id),
        vehicle_id=UUID(veh_id),
        accident_date=date.today(),
        accident_location="Cruce concurrente",
    )
    db_session.add(cr)
    await db_session.commit()
    req_id = str(cr.id)

    r1, r2 = await asyncio.gather(
        async_client.post(f"/api/claim-requests/{req_id}/take", headers=_headers(token)),
        async_client.post(f"/api/claim-requests/{req_id}/take", headers=_headers(token)),
    )

    statuses = sorted([r1.status_code, r2.status_code])
    assert statuses == [200, 409], f"Esperado [200, 409], obtenido {statuses}"


@pytest.mark.asyncio
async def test_reject_at_intake(async_client, db_session, user_admin):
    token = await _login(async_client)
    ph_id = await _create_policyholder(async_client, token, "CL-RJ")
    pol_id = await _create_policy(async_client, token, ph_id, "CL-RJ")
    veh_id = await _create_vehicle(async_client, token, pol_id, "CL-RJ")

    cr = ClaimRequest(
        tenant_id=user_admin.tenant_id,
        status=ClaimRequestStatus.SUBMITTED,
        request_number="REQ-TO-REJECT",
        policyholder_id=UUID(ph_id),
        policy_id=UUID(pol_id),
        vehicle_id=UUID(veh_id),
        accident_date=date.today(),
        accident_location="Av. Rechazo 456",
    )
    db_session.add(cr)
    await db_session.commit()
    req_id = str(cr.id)

    resp = await async_client.post(
        f"/api/claim-requests/{req_id}/take",
        headers=_headers(token),
    )
    assert resp.status_code == 200

    resp = await async_client.post(
        f"/api/claim-requests/{req_id}/reject",
        json={"reason": "Datos claramente inválidos, póliza no corresponde al titular reportado."},
        headers=_headers(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "rejected_at_intake"
    assert data["intake_decision_reason"] is not None


# ─── Status transitions ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_claim_status(async_client, user_admin):
    token = await _login(async_client)
    ph_id = await _create_policyholder(async_client, token, "CL-US")
    pol_id = await _create_policy(async_client, token, ph_id, "CL-US")
    veh_id = await _create_vehicle(async_client, token, pol_id, "CL-US")

    resp = await async_client.post(
        "/api/claims",
        json={
            "policyholder_id": ph_id,
            "policy_id": pol_id,
            "vehicle_id": veh_id,
            "accident_date": str(date.today()),
            "accident_location": "Calle 9",
        },
        headers=_headers(token),
    )
    claim_id = resp.json()["id"]

    resp = await async_client.patch(
        f"/api/claims/{claim_id}/status",
        json={"new_status": "in_review", "reason": "Inicio de revisión del caso"},
        headers=_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_review"


@pytest.mark.asyncio
async def test_invalid_transition(async_client, user_admin):
    token = await _login(async_client)
    ph_id = await _create_policyholder(async_client, token, "CL-IVT")
    pol_id = await _create_policy(async_client, token, ph_id, "CL-IVT")
    veh_id = await _create_vehicle(async_client, token, pol_id, "CL-IVT")

    resp = await async_client.post(
        "/api/claims",
        json={
            "policyholder_id": ph_id,
            "policy_id": pol_id,
            "vehicle_id": veh_id,
            "accident_date": str(date.today()),
            "accident_location": "Av. Inválida 0",
        },
        headers=_headers(token),
    )
    claim_id = resp.json()["id"]

    resp = await async_client.patch(
        f"/api/claims/{claim_id}/status",
        json={"new_status": "closed"},
        headers=_headers(token),
    )
    assert resp.status_code == 422


# ─── Observations ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_observation(async_client, user_admin):
    token = await _login(async_client)
    ph_id = await _create_policyholder(async_client, token, "CL-OB")
    pol_id = await _create_policy(async_client, token, ph_id, "CL-OB")
    veh_id = await _create_vehicle(async_client, token, pol_id, "CL-OB")

    resp = await async_client.post(
        "/api/claims",
        json={
            "policyholder_id": ph_id,
            "policy_id": pol_id,
            "vehicle_id": veh_id,
            "accident_date": str(date.today()),
            "accident_location": "Barrio Observación",
        },
        headers=_headers(token),
    )
    claim_id = resp.json()["id"]

    resp = await async_client.post(
        f"/api/claims/{claim_id}/observations",
        json={"comment": "Revisar cobertura del siniestro."},
        headers=_headers(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["comment"] == "Revisar cobertura del siniestro."
    assert data["claim_id"] == claim_id


@pytest.mark.asyncio
async def test_list_observations(async_client, user_admin):
    token = await _login(async_client)
    ph_id = await _create_policyholder(async_client, token, "CL-OL")
    pol_id = await _create_policy(async_client, token, ph_id, "CL-OL")
    veh_id = await _create_vehicle(async_client, token, pol_id, "CL-OL")

    resp = await async_client.post(
        "/api/claims",
        json={
            "policyholder_id": ph_id,
            "policy_id": pol_id,
            "vehicle_id": veh_id,
            "accident_date": str(date.today()),
            "accident_location": "Observatorio Sur",
        },
        headers=_headers(token),
    )
    claim_id = resp.json()["id"]

    await async_client.post(
        f"/api/claims/{claim_id}/observations",
        json={"comment": "Observación 1"},
        headers=_headers(token),
    )

    resp = await async_client.get(
        f"/api/claims/{claim_id}/observations",
        headers=_headers(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1


# ─── Third Parties ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_third_party(async_client, user_admin):
    token = await _login(async_client)
    ph_id = await _create_policyholder(async_client, token, "CL-TP")
    pol_id = await _create_policy(async_client, token, ph_id, "CL-TP")
    veh_id = await _create_vehicle(async_client, token, pol_id, "CL-TP")

    resp = await async_client.post(
        "/api/claims",
        json={
            "policyholder_id": ph_id,
            "policy_id": pol_id,
            "vehicle_id": veh_id,
            "accident_date": str(date.today()),
            "accident_location": "Cruce Peligroso",
        },
        headers=_headers(token),
    )
    claim_id = resp.json()["id"]

    resp = await async_client.post(
        f"/api/claims/{claim_id}/third-parties",
        json={"kind": "driver", "full_name": "Juan Pérez"},
        headers=_headers(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["full_name"] == "Juan Pérez"
    assert data["kind"] == "driver"
    assert data["claim_id"] == claim_id


@pytest.mark.asyncio
async def test_list_third_parties(async_client, user_admin):
    token = await _login(async_client)
    ph_id = await _create_policyholder(async_client, token, "CL-TL")
    pol_id = await _create_policy(async_client, token, ph_id, "CL-TL")
    veh_id = await _create_vehicle(async_client, token, pol_id, "CL-TL")

    resp = await async_client.post(
        "/api/claims",
        json={
            "policyholder_id": ph_id,
            "policy_id": pol_id,
            "vehicle_id": veh_id,
            "accident_date": str(date.today()),
            "accident_location": "Rotonda Sur",
        },
        headers=_headers(token),
    )
    claim_id = resp.json()["id"]

    await async_client.post(
        f"/api/claims/{claim_id}/third-parties",
        json={"kind": "witness", "full_name": "María López"},
        headers=_headers(token),
    )

    resp = await async_client.get(
        f"/api/claims/{claim_id}/third-parties",
        headers=_headers(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_delete_third_party(async_client, user_admin):
    token = await _login(async_client)
    ph_id = await _create_policyholder(async_client, token, "CL-TD")
    pol_id = await _create_policy(async_client, token, ph_id, "CL-TD")
    veh_id = await _create_vehicle(async_client, token, pol_id, "CL-TD")

    resp = await async_client.post(
        "/api/claims",
        json={
            "policyholder_id": ph_id,
            "policy_id": pol_id,
            "vehicle_id": veh_id,
            "accident_date": str(date.today()),
            "accident_location": "Esquina Olvidada",
        },
        headers=_headers(token),
    )
    claim_id = resp.json()["id"]

    resp = await async_client.post(
        f"/api/claims/{claim_id}/third-parties",
        json={"kind": "victim", "full_name": "Carlos Ruiz"},
        headers=_headers(token),
    )
    tp_id = resp.json()["id"]

    resp = await async_client.delete(
        f"/api/claims/{claim_id}/third-parties/{tp_id}",
        headers=_headers(token),
    )
    assert resp.status_code == 204

    resp = await async_client.get(
        f"/api/claims/{claim_id}/third-parties",
        headers=_headers(token),
    )
    assert resp.json()["total"] == 0
