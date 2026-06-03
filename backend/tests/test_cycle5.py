"""Tests for Cycle 5: Notifications, Escalation, Decision, Assignment."""

import pytest
from httpx import AsyncClient
from datetime import date, timedelta


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "X-Tenant-Slug": "aseguradora-a"}


async def _login(async_client: AsyncClient, email: str = "admin@aseguradora-a.com") -> str:
    resp = await async_client.post(
        "/api/auth/login",
        json={"email": email, "password": "Password123!"},
        headers={"X-Tenant-Slug": "aseguradora-a"},
    )
    data = resp.json()
    return data["access_token"]


async def _create_policyholder(async_client: AsyncClient, token: str, suffix: str = "") -> str:
    key = f"PH-C5-{suffix}"
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
            "policy_number": f"POL-C5-{suffix}",
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
            "plate": f"PL-C5-{suffix}",
            "make": "Toyota",
            "model": "Corolla",
            "year": 2022,
            "vehicle_type": "sedan",
            "policy_id": policy_id,
        },
        headers=_headers(token),
    )
    return resp.json()["id"]


async def _create_claim(async_client: AsyncClient, token: str) -> str:
    ph_id = await _create_policyholder(async_client, token, "C")
    pol_id = await _create_policy(async_client, token, ph_id, "C")
    veh_id = await _create_vehicle(async_client, token, pol_id, "C")
    resp = await async_client.post(
        "/api/claims",
        json={
            "policyholder_id": ph_id,
            "policy_id": pol_id,
            "vehicle_id": veh_id,
            "accident_date": str(date.today()),
            "accident_location": "Calle 10 #5-20, Bogotá",
            "accident_description": "Colisión lateral en intersección",
        },
        headers=_headers(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _move_claim_to(async_client: AsyncClient, token: str, claim_id: str, target_status: str):
    reason_map = {
        "in_review": "Iniciando revisión",
        "observed": "Observación detectada en fotos del siniestro",
        "in_evaluation": "Pasando a evaluación",
        "closed": "Cerrando expediente",
    }
    resp = await async_client.patch(
        f"/api/claims/{claim_id}/status",
        json={
            "new_status": target_status,
            "reason": reason_map.get(target_status, f"Moving to {target_status}"),
        },
        headers=_headers(token),
    )
    assert resp.status_code == 200, f"Failed moving to {target_status}: {resp.text}"
    return resp


# ─── Notifications (CU-27) ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_notifications_empty(async_client, user_admin):
    token = await _login(async_client)
    resp = await async_client.get("/api/me/notifications", headers=_headers(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["unread_count"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_mark_all_read_no_notifications(async_client, user_admin):
    token = await _login(async_client)
    resp = await async_client.post("/api/me/notifications/mark-all-read", headers=_headers(token))
    assert resp.status_code == 200
    data = resp.json()
    assert "marked_read" in data


# ─── Assign Analyst (CU-26) ────────────────────────────────────────


@pytest.mark.asyncio
async def test_assign_analyst_success(async_client, user_admin, user_analyst):
    """Admin assigns an active analyst to a claim."""
    token = await _login(async_client)
    claim_id = await _create_claim(async_client, token)

    resp = await async_client.patch(
        f"/api/claims/{claim_id}/assign",
        json={"analyst_user_id": str(user_analyst.id), "reason": "Redistribución de carga"},
        headers=_headers(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["assigned_analyst_id"] == str(user_analyst.id)


@pytest.mark.asyncio
async def test_assign_analyst_non_analyst_target(async_client, user_admin, user_supervisor):
    """Assigning to a supervisor (non-analyst) must fail with 422."""
    token = await _login(async_client)
    claim_id = await _create_claim(async_client, token)

    resp = await async_client.patch(
        f"/api/claims/{claim_id}/assign",
        json={"analyst_user_id": str(user_supervisor.id), "reason": "Test"},
        headers=_headers(token),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_assign_analyst_closed_claim(async_client, user_admin, user_analyst):
    """Cannot reassign a closed claim."""
    token = await _login(async_client)
    claim_id = await _create_claim(async_client, token)

    await _move_claim_to(async_client, token, claim_id, "in_review")
    await _move_claim_to(async_client, token, claim_id, "in_evaluation")

    # Approve
    resp = await async_client.post(
        f"/api/claims/{claim_id}/decision",
        json={"decision": "approved", "reason": "Todo en orden"},
        headers=_headers(token),
    )
    assert resp.status_code == 200

    # Close
    await _move_claim_to(async_client, token, claim_id, "closed")

    resp = await async_client.patch(
        f"/api/claims/{claim_id}/assign",
        json={"analyst_user_id": str(user_analyst.id)},
        headers=_headers(token),
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_assign_analyst_insufficient_permissions(async_client, user_admin, user_analyst):
    """Analyst cannot reassign claims."""
    token = await _login(async_client)
    claim_id = await _create_claim(async_client, token)

    analyst_token = await _login(async_client, "analyst@aseguradora-a.com")
    resp = await async_client.patch(
        f"/api/claims/{claim_id}/assign",
        json={"analyst_user_id": str(user_analyst.id)},
        headers=_headers(analyst_token),
    )
    assert resp.status_code == 403


# ─── Escalate (CU-19) ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_escalate_success(async_client, user_admin, user_analyst, user_supervisor):
    """Analyst escalates a claim to a supervisor."""
    token = await _create_and_login_analyst(async_client, user_admin)
    claim_id = await _create_claim(async_client, token)

    await _move_claim_to(async_client, token, claim_id, "in_review")
    await _move_claim_to(async_client, token, claim_id, "in_evaluation")

    resp = await async_client.post(
        f"/api/claims/{claim_id}/escalate",
        json={"supervisor_user_id": str(user_supervisor.id), "reason": "Caso complejo, requiere revisión experta"},
        headers=_headers(token),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["supervisor_id"] == str(user_supervisor.id)


async def _create_and_login_analyst(async_client, user_admin):
    """Helper: login as admin, create analyst user, then login as analyst."""
    admin_token = await _login(async_client)
    return await _login(async_client, "analyst@aseguradora-a.com")


@pytest.mark.asyncio
async def test_escalate_registered_fails(async_client, user_admin, user_analyst, user_supervisor):
    """Cannot escalate a claim in 'registered' state."""
    analyst_token = await _login(async_client, "analyst@aseguradora-a.com")
    claim_id = await _create_claim(async_client, analyst_token)

    resp = await async_client.post(
        f"/api/claims/{claim_id}/escalate",
        json={"supervisor_user_id": str(user_supervisor.id), "reason": "Test"},
        headers=_headers(analyst_token),
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_escalate_already_escalated(async_client, user_admin, user_analyst, user_supervisor):
    """Cannot escalate a claim that is already escalated."""
    analyst_token = await _login(async_client, "analyst@aseguradora-a.com")
    claim_id = await _create_claim(async_client, analyst_token)

    await _move_claim_to(async_client, analyst_token, claim_id, "in_review")
    await _move_claim_to(async_client, analyst_token, claim_id, "in_evaluation")

    # First escalation
    resp = await async_client.post(
        f"/api/claims/{claim_id}/escalate",
        json={"supervisor_user_id": str(user_supervisor.id), "reason": "Primera escalación"},
        headers=_headers(analyst_token),
    )
    assert resp.status_code == 200

    # Second escalation
    resp = await async_client.post(
        f"/api/claims/{claim_id}/escalate",
        json={"supervisor_user_id": str(user_supervisor.id), "reason": "Segunda"},
        headers=_headers(analyst_token),
    )
    assert resp.status_code == 409


# ─── Decision (CU-20) ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_decide_approve_success(async_client, user_admin):
    """Admin approves a claim in in_evaluation."""
    token = await _login(async_client)
    claim_id = await _create_claim(async_client, token)

    await _move_claim_to(async_client, token, claim_id, "in_review")
    await _move_claim_to(async_client, token, claim_id, "in_evaluation")

    resp = await async_client.post(
        f"/api/claims/{claim_id}/decision",
        json={"decision": "approved", "reason": "Toda la documentación es consistente"},
        headers=_headers(token),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "approved"
    assert data["decision"] == "approved"
    assert data["decision_reason"] == "Toda la documentación es consistente"
    assert data["decided_by_user_id"] is not None


@pytest.mark.asyncio
async def test_decide_reject_success(async_client, user_admin):
    """Admin rejects a claim in in_evaluation."""
    token = await _login(async_client)
    claim_id = await _create_claim(async_client, token)

    await _move_claim_to(async_client, token, claim_id, "in_review")
    await _move_claim_to(async_client, token, claim_id, "in_evaluation")

    resp = await async_client.post(
        f"/api/claims/{claim_id}/decision",
        json={"decision": "rejected", "reason": "Póliza no cubre el tipo de siniestro"},
        headers=_headers(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "rejected"
    assert data["decision"] == "rejected"


@pytest.mark.asyncio
async def test_decide_not_in_evaluation_fails(async_client, user_admin):
    """Cannot decide on a claim not in in_evaluation."""
    token = await _login(async_client)
    claim_id = await _create_claim(async_client, token)

    resp = await async_client.post(
        f"/api/claims/{claim_id}/decision",
        json={"decision": "approved", "reason": "Test"},
        headers=_headers(token),
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_decide_already_decided_fails(async_client, user_admin):
    """Cannot decide twice on the same claim."""
    token = await _login(async_client)
    claim_id = await _create_claim(async_client, token)

    await _move_claim_to(async_client, token, claim_id, "in_review")
    await _move_claim_to(async_client, token, claim_id, "in_evaluation")

    resp = await async_client.post(
        f"/api/claims/{claim_id}/decision",
        json={"decision": "approved", "reason": "OK"},
        headers=_headers(token),
    )
    assert resp.status_code == 200

    resp = await async_client.post(
        f"/api/claims/{claim_id}/decision",
        json={"decision": "rejected", "reason": "Cambio de opinión"},
        headers=_headers(token),
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_decide_insufficient_permissions(async_client, user_admin, user_analyst):
    """Analyst cannot approve/reject claims."""
    admin_token = await _login(async_client)
    claim_id = await _create_claim(async_client, admin_token)

    await _move_claim_to(async_client, admin_token, claim_id, "in_review")
    await _move_claim_to(async_client, admin_token, claim_id, "in_evaluation")

    analyst_token = await _login(async_client, "analyst@aseguradora-a.com")
    resp = await async_client.post(
        f"/api/claims/{claim_id}/decision",
        json={"decision": "approved", "reason": "Yo decido"},
        headers=_headers(analyst_token),
    )
    assert resp.status_code == 403


# ─── Notifications after actions ───────────────────────────────────


@pytest.mark.asyncio
async def test_notification_created_on_assign(async_client, user_admin, user_analyst):
    """Reassigning creates notification for the new analyst."""
    token = await _login(async_client)
    claim_id = await _create_claim(async_client, token)

    await async_client.patch(
        f"/api/claims/{claim_id}/assign",
        json={"analyst_user_id": str(user_analyst.id), "reason": "Asignación inicial"},
        headers=_headers(token),
    )

    analyst_token = await _login(async_client, "analyst@aseguradora-a.com")
    resp = await async_client.get("/api/me/notifications", headers=_headers(analyst_token))
    assert resp.status_code == 200
    data = resp.json()
    found = any(n["kind"] == "assigned" for n in data["items"])
    assert found, "Analyst should receive an 'assigned' notification"


@pytest.mark.asyncio
async def test_notification_created_on_escalate(async_client, user_admin, user_analyst, user_supervisor):
    """Escalating creates notification for the supervisor."""
    analyst_token = await _login(async_client, "analyst@aseguradora-a.com")
    claim_id = await _create_claim(async_client, analyst_token)

    await _move_claim_to(async_client, analyst_token, claim_id, "in_review")
    await _move_claim_to(async_client, analyst_token, claim_id, "in_evaluation")

    await async_client.post(
        f"/api/claims/{claim_id}/escalate",
        json={"supervisor_user_id": str(user_supervisor.id), "reason": "Escalar para revisión"},
        headers=_headers(analyst_token),
    )

    sup_token = await _login(async_client, "supervisor@aseguradora-a.com")
    resp = await async_client.get("/api/me/notifications", headers=_headers(sup_token))
    data = resp.json()
    found = any(n["kind"] == "escalated" for n in data["items"])
    assert found, "Supervisor should receive an 'escalated' notification"
