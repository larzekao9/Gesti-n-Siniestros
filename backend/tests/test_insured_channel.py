"""Tests del Ciclo 7 — Canal del Asegurado (CU-01..CU-08).

Cubre: invitación + registro + login (CU-01), borrador + envío (CU-02/03/05),
evidencias del asegurado (CU-04), consulta de estado (CU-06), aislamiento por
cuenta y por scope, y los retro-enganches de notificación (CU-25 → asegurado).
"""

from datetime import date, timedelta

import pytest
from httpx import AsyncClient


TENANT = "aseguradora-a"


def _h(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "X-Tenant-Slug": TENANT}


# ── helpers internos (analista/admin) ─────────────────────────────────


async def _login_internal(async_client: AsyncClient, email: str) -> str:
    resp = await async_client.post(
        "/api/auth/login",
        json={"email": email, "password": "Password123!"},
        headers={"X-Tenant-Slug": TENANT},
    )
    return resp.json()["access_token"]


async def _make_catalog(async_client: AsyncClient, token: str, suffix: str) -> dict:
    today = date.today()
    ph = await async_client.post(
        "/api/policyholders",
        json={
            "document_id": f"DOC-{suffix}",
            "full_name": f"Asegurado {suffix}",
            "phone": "70000000",
            "email": f"asegurado-{suffix}@mail.com",
        },
        headers=_h(token),
    )
    ph_id = ph.json()["id"]
    pol = await async_client.post(
        "/api/policies",
        json={
            "policy_number": f"POL-{suffix}",
            "policyholder_id": ph_id,
            "valid_from": str(today),
            "valid_to": str(today + timedelta(days=365)),
            "coverage_type": "full",
        },
        headers=_h(token),
    )
    pol_id = pol.json()["id"]
    veh = await async_client.post(
        "/api/vehicles",
        json={
            "plate": f"PL-{suffix}",
            "make": "Toyota",
            "model": "Corolla",
            "year": 2022,
            "vehicle_type": "sedan",
            "policy_id": pol_id,
        },
        headers=_h(token),
    )
    return {"ph_id": ph_id, "pol_id": pol_id, "veh_id": veh.json()["id"]}


async def _invite_and_register(
    async_client: AsyncClient, admin_token: str, ph_id: str, password="Insured123!"
) -> dict:
    inv = await async_client.post(
        f"/api/policyholders/{ph_id}/invite", headers=_h(admin_token)
    )
    assert inv.status_code == 200, inv.text
    token = inv.json()["activation_token"]
    reg = await async_client.post(
        "/api/insured-auth/register",
        json={"activation_token": token, "password": password},
    )
    assert reg.status_code == 200, reg.text
    return reg.json()


async def _full_account(async_client: AsyncClient, suffix: str) -> dict:
    """Crea catálogo + cuenta de asegurado activa. Devuelve ids + access_token insured."""
    admin = await _login_internal(async_client, "admin@aseguradora-a.com")
    cat = await _make_catalog(async_client, admin, suffix)
    reg = await _invite_and_register(async_client, admin, cat["ph_id"])
    return {**cat, "admin_token": admin, "access_token": reg["access_token"]}


async def _create_submittable_draft(
    async_client: AsyncClient, acc: dict
) -> str:
    """Crea un draft completo + 1 evidencia → listo para submit."""
    token = acc["access_token"]
    draft = await async_client.post(
        "/api/me/claim-requests",
        json={
            "policyholder_id": acc["ph_id"],
            "policy_id": acc["pol_id"],
            "vehicle_id": acc["veh_id"],
            "accident_date": str(date.today()),
            "accident_location": "Av. Test 123",
            "accident_description": "Choque leve en intersección",
        },
        headers=_h(token),
    )
    assert draft.status_code == 201, draft.text
    req_id = draft.json()["id"]
    ev = await async_client.post(
        f"/api/me/claim-requests/{req_id}/evidences",
        json={
            "s3_key": "tenants/x/claim_request/y/photo.jpg",
            "type": "photo",
            "file_name": "photo.jpg",
            "mime_type": "image/jpeg",
            "file_size": 1024,
        },
        headers=_h(token),
    )
    assert ev.status_code == 201, ev.text
    return req_id


# ── CU-01: invitación + registro + login ──────────────────────────────


@pytest.mark.asyncio
async def test_invite_register_login_happy(async_client, user_admin):
    admin = await _login_internal(async_client, "admin@aseguradora-a.com")
    cat = await _make_catalog(async_client, admin, "INV")

    inv = await async_client.post(
        f"/api/policyholders/{cat['ph_id']}/invite", headers=_h(admin)
    )
    assert inv.status_code == 200
    assert inv.json()["activation_token"]

    reg = await _invite_and_register(async_client, admin, cat["ph_id"])
    assert reg["account"]["is_active"] is True

    login = await async_client.post(
        "/api/insured-auth/login",
        json={
            "email": cat and inv.json()["email"],
            "password": "Insured123!",
            "tenant_slug": TENANT,
        },
    )
    assert login.status_code == 200
    assert login.json()["access_token"]


@pytest.mark.asyncio
async def test_register_invalid_token(async_client, user_admin):
    resp = await async_client.post(
        "/api/insured-auth/register",
        json={"activation_token": "no-existe-token-xxxx", "password": "Insured123!"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_invite_twice_conflicts_after_active(async_client, user_admin):
    admin = await _login_internal(async_client, "admin@aseguradora-a.com")
    cat = await _make_catalog(async_client, admin, "DUP")
    await _invite_and_register(async_client, admin, cat["ph_id"])
    # Ya activa → segunda invitación es 409.
    inv = await async_client.post(
        f"/api/policyholders/{cat['ph_id']}/invite", headers=_h(admin)
    )
    assert inv.status_code == 409


@pytest.mark.asyncio
async def test_insured_login_wrong_password(async_client, user_admin):
    await _full_account(async_client, "WP")
    resp = await async_client.post(
        "/api/insured-auth/login",
        json={
            "email": "asegurado-WP@mail.com",
            "password": "WRONG",
            "tenant_slug": TENANT,
        },
    )
    assert resp.status_code == 401


# ── CU-02/03/05: borrador y envío ─────────────────────────────────────


@pytest.mark.asyncio
async def test_submit_incomplete_without_evidence(async_client, user_admin):
    acc = await _full_account(async_client, "INC")
    draft = await async_client.post(
        "/api/me/claim-requests",
        json={
            "policyholder_id": acc["ph_id"],
            "policy_id": acc["pol_id"],
            "vehicle_id": acc["veh_id"],
            "accident_date": str(date.today()),
            "accident_location": "Av. Test 123",
            "accident_description": "Choque",
        },
        headers=_h(acc["access_token"]),
    )
    req_id = draft.json()["id"]
    resp = await async_client.post(
        f"/api/me/claim-requests/{req_id}/submit", headers=_h(acc["access_token"])
    )
    assert resp.status_code == 422
    assert "evidences" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_submit_happy_assigns_request_number(async_client, user_admin):
    acc = await _full_account(async_client, "SUB")
    req_id = await _create_submittable_draft(async_client, acc)
    resp = await async_client.post(
        f"/api/me/claim-requests/{req_id}/submit", headers=_h(acc["access_token"])
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "submitted"
    assert data["request_number"].startswith("REQ-")


@pytest.mark.asyncio
async def test_submit_twice_conflicts(async_client, user_admin):
    acc = await _full_account(async_client, "SUB2")
    req_id = await _create_submittable_draft(async_client, acc)
    await async_client.post(
        f"/api/me/claim-requests/{req_id}/submit", headers=_h(acc["access_token"])
    )
    resp = await async_client.post(
        f"/api/me/claim-requests/{req_id}/submit", headers=_h(acc["access_token"])
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_delete_draft_then_404(async_client, user_admin):
    acc = await _full_account(async_client, "DEL")
    draft = await async_client.post(
        "/api/me/claim-requests",
        json={
            "policyholder_id": acc["ph_id"],
            "policy_id": acc["pol_id"],
            "vehicle_id": acc["veh_id"],
        },
        headers=_h(acc["access_token"]),
    )
    req_id = draft.json()["id"]
    d = await async_client.delete(
        f"/api/me/claim-requests/{req_id}", headers=_h(acc["access_token"])
    )
    assert d.status_code == 204
    g = await async_client.get(
        f"/api/me/claim-requests/{req_id}", headers=_h(acc["access_token"])
    )
    assert g.status_code == 404


# ── Aislamiento por cuenta y por scope ────────────────────────────────


@pytest.mark.asyncio
async def test_cross_account_isolation_returns_404(async_client, user_admin):
    acc_a = await _full_account(async_client, "ISOA")
    acc_b = await _full_account(async_client, "ISOB")
    req_id = await _create_submittable_draft(async_client, acc_a)
    # B intenta leer la solicitud de A.
    resp = await async_client.get(
        f"/api/me/claim-requests/{req_id}", headers=_h(acc_b["access_token"])
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_internal_token_rejected_on_me_endpoints(async_client, user_admin):
    admin = await _login_internal(async_client, "admin@aseguradora-a.com")
    resp = await async_client.get("/api/me/claim-requests", headers=_h(admin))
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_insured_token_rejected_on_internal_endpoints(async_client, user_admin):
    acc = await _full_account(async_client, "SCOPE")
    resp = await async_client.get(
        "/api/policyholders", headers=_h(acc["access_token"])
    )
    assert resp.status_code == 401


# ── CU-06: consulta de estado + retro-enganche CU-25 ──────────────────


@pytest.mark.asyncio
async def test_reject_at_intake_notifies_insured(
    async_client, user_admin, user_analyst
):
    acc = await _full_account(async_client, "REJ")
    req_id = await _create_submittable_draft(async_client, acc)
    await async_client.post(
        f"/api/me/claim-requests/{req_id}/submit", headers=_h(acc["access_token"])
    )

    analyst = await _login_internal(async_client, "analyst@aseguradora-a.com")
    take = await async_client.post(
        f"/api/claim-requests/{req_id}/take", headers=_h(analyst)
    )
    assert take.status_code == 200, take.text
    rej = await async_client.post(
        f"/api/claim-requests/{req_id}/reject",
        json={"reason": "Datos del siniestro claramente inconsistentes con la póliza."},
        headers=_h(analyst),
    )
    assert rej.status_code == 200, rej.text

    # El asegurado debe ver una notificación de rechazo.
    notifs = await async_client.get(
        "/api/me/notifications", headers=_h(acc["access_token"])
    )
    assert notifs.status_code == 200
    kinds = [n["kind"] for n in notifs.json()["items"]]
    assert "intake_rejected" in kinds


@pytest.mark.asyncio
async def test_list_my_claim_requests(async_client, user_admin):
    acc = await _full_account(async_client, "LIST")
    await _create_submittable_draft(async_client, acc)
    resp = await async_client.get(
        "/api/me/claim-requests", headers=_h(acc["access_token"])
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


# ── Catálogo del asegurado (wizard CU-02 paso 1) ──────────────────────


@pytest.mark.asyncio
async def test_my_vehicles_and_policies_scoped(async_client, user_admin):
    acc = await _full_account(async_client, "CAT")
    veh = await async_client.get("/api/me/vehicles", headers=_h(acc["access_token"]))
    assert veh.status_code == 200
    plates = [v["plate"] for v in veh.json()]
    assert "PL-CAT" in plates

    pol = await async_client.get("/api/me/policies", headers=_h(acc["access_token"]))
    assert pol.status_code == 200
    assert any(p["policy_number"] == "POL-CAT" for p in pol.json())


@pytest.mark.asyncio
async def test_my_vehicles_only_own_policyholder(async_client, user_admin):
    acc_a = await _full_account(async_client, "OWNA")
    await _full_account(async_client, "OWNB")  # crea la cuenta B (efecto necesario)
    # A no debe ver el vehículo de B.
    veh_a = await async_client.get("/api/me/vehicles", headers=_h(acc_a["access_token"]))
    plates = [v["plate"] for v in veh_a.json()]
    assert "PL-OWNA" in plates
    assert "PL-OWNB" not in plates


@pytest.mark.asyncio
async def test_draft_forces_own_policyholder(async_client, user_admin):
    """Aunque el cliente mande otro policyholder_id, se fuerza el de la cuenta."""
    acc_a = await _full_account(async_client, "FORCEA")
    acc_b = await _full_account(async_client, "FORCEB")
    draft = await async_client.post(
        "/api/me/claim-requests",
        json={
            "policyholder_id": acc_b["ph_id"],  # intento de suplantación
            "policy_id": acc_a["pol_id"],
            "vehicle_id": acc_a["veh_id"],
        },
        headers=_h(acc_a["access_token"]),
    )
    assert draft.status_code == 201
    assert draft.json()["policyholder_id"] == acc_a["ph_id"]
