"""Tests for Cycle 4: Evidences, Document Requests, Traffic Reports."""

import pytest
from httpx import AsyncClient
from datetime import date, timedelta

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
    resp = await async_client.post(
        "/api/policyholders",
        json={"document_id": f"EVI-{suffix}", "full_name": f"Evid Holder {suffix}", "phone": "3100000"},
        headers=_headers(token),
    )
    return resp.json()["id"]


async def _create_policy(async_client: AsyncClient, token: str, ph_id: str, suffix: str = "") -> str:
    today = date.today()
    resp = await async_client.post(
        "/api/policies",
        json={
            "policy_number": f"POL-EVI-{suffix}",
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
            "plate": f"EVI-{suffix}",
            "make": "Honda",
            "model": "Civic",
            "year": 2023,
            "vehicle_type": "sedan",
            "policy_id": policy_id,
        },
        headers=_headers(token),
    )
    return resp.json()["id"]


async def _create_claim(async_client: AsyncClient, token: str, ph_id: str, pol_id: str, veh_id: str, suffix: str = "") -> dict:
    resp = await async_client.post(
        "/api/claims",
        json={
            "policyholder_id": ph_id,
            "policy_id": pol_id,
            "vehicle_id": veh_id,
            "accident_date": str(date.today()),
            "accident_location": f"Location {suffix}",
        },
        headers=_headers(token),
    )
    return resp.json()


# ── Evidence presigned URL ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_presigned_url_success(async_client, user_admin):
    token = await _login(async_client)
    ph_id = await _create_policyholder(async_client, token, "PRE")
    pol_id = await _create_policy(async_client, token, ph_id, "PRE")
    veh_id = await _create_vehicle(async_client, token, pol_id, "PRE")
    claim = await _create_claim(async_client, token, ph_id, pol_id, veh_id, "PRE")

    resp = await async_client.post(
        "/api/evidences/presign",
        json={
            "subject_type": "claim",
            "subject_id": claim["id"],
            "type": "photo",
            "file_name": "test.jpg",
            "mime_type": "image/jpeg",
            "file_size": 1024,
        },
        headers=_headers(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "upload_url" in data
    assert "s3_key" in data


@pytest.mark.asyncio
async def test_presigned_url_invalid_mime(async_client, user_admin):
    token = await _login(async_client)
    resp = await async_client.post(
        "/api/evidences/presign",
        json={
            "subject_type": "claim",
            "subject_id": "00000000-0000-0000-0000-000000000001",
            "type": "photo",
            "file_name": "malware.exe",
            "mime_type": "application/x-msdownload",
            "file_size": 1024,
        },
        headers=_headers(token),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_presigned_url_file_too_large(async_client, user_admin):
    token = await _login(async_client)
    resp = await async_client.post(
        "/api/evidences/presign",
        json={
            "subject_type": "claim",
            "subject_id": "00000000-0000-0000-0000-000000000001",
            "type": "photo",
            "file_name": "huge.jpg",
            "mime_type": "image/jpeg",
            "file_size": 100 * 1024 * 1024,  # 100 MB, exceeds 50 MB max
        },
        headers=_headers(token),
    )
    assert resp.status_code == 422


# ── Document Requests ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_document_request(async_client, user_admin):
    token = await _login(async_client)
    ph_id = await _create_policyholder(async_client, token, "DR")
    pol_id = await _create_policy(async_client, token, ph_id, "DR")
    veh_id = await _create_vehicle(async_client, token, pol_id, "DR")
    claim = await _create_claim(async_client, token, ph_id, pol_id, veh_id, "DR")

    resp = await async_client.post(
        "/api/document-requests?claim_id=" + claim["id"],
        json={"description": "Adjuntar factura de taller"},
        headers=_headers(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "pending"
    assert data["description"] == "Adjuntar factura de taller"
    assert data["claim_id"] == claim["id"]


@pytest.mark.asyncio
async def test_submit_document_request(async_client, user_admin):
    token = await _login(async_client)
    ph_id = await _create_policyholder(async_client, token, "DRS")
    pol_id = await _create_policy(async_client, token, ph_id, "DRS")
    veh_id = await _create_vehicle(async_client, token, pol_id, "DRS")
    claim = await _create_claim(async_client, token, ph_id, pol_id, veh_id, "DRS")

    dr_resp = await async_client.post(
        "/api/document-requests?claim_id=" + claim["id"],
        json={"description": "Fotos del otro vehículo"},
        headers=_headers(token),
    )
    dr_id = dr_resp.json()["id"]

    resp = await async_client.post(
        f"/api/document-requests/{dr_id}/submit",
        headers=_headers(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "submitted"
    assert data["resolved_at"] is not None


@pytest.mark.asyncio
async def test_waive_document_request(async_client, user_admin):
    token = await _login(async_client)
    ph_id = await _create_policyholder(async_client, token, "DRW")
    pol_id = await _create_policy(async_client, token, ph_id, "DRW")
    veh_id = await _create_vehicle(async_client, token, pol_id, "DRW")
    claim = await _create_claim(async_client, token, ph_id, pol_id, veh_id, "DRW")

    dr_resp = await async_client.post(
        "/api/document-requests?claim_id=" + claim["id"],
        json={"description": "Documento no relevante"},
        headers=_headers(token),
    )
    dr_id = dr_resp.json()["id"]

    resp = await async_client.post(
        f"/api/document-requests/{dr_id}/waive",
        headers=_headers(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "waived"


@pytest.mark.asyncio
async def test_submit_twice_fails(async_client, user_admin):
    token = await _login(async_client)
    ph_id = await _create_policyholder(async_client, token, "DR2X")
    pol_id = await _create_policy(async_client, token, ph_id, "DR2X")
    veh_id = await _create_vehicle(async_client, token, pol_id, "DR2X")
    claim = await _create_claim(async_client, token, ph_id, pol_id, veh_id, "DR2X")

    dr_resp = await async_client.post(
        "/api/document-requests?claim_id=" + claim["id"],
        json={"description": "Una vez"},
        headers=_headers(token),
    )
    dr_id = dr_resp.json()["id"]

    await async_client.post(f"/api/document-requests/{dr_id}/submit", headers=_headers(token))
    resp = await async_client.post(f"/api/document-requests/{dr_id}/submit", headers=_headers(token))
    assert resp.status_code == 409


# ── Traffic Reports ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_traffic_report(async_client, user_admin):
    token = await _login(async_client)
    ph_id = await _create_policyholder(async_client, token, "TR")
    pol_id = await _create_policy(async_client, token, ph_id, "TR")
    veh_id = await _create_vehicle(async_client, token, pol_id, "TR")
    claim = await _create_claim(async_client, token, ph_id, pol_id, veh_id, "TR")

    resp = await async_client.post(
        "/api/traffic-reports?claim_id=" + claim["id"],
        json={
            "officer_name": "Oficial Perez",
            "report_code": "ACT-2026-001",
            "jurisdiction": "La Paz",
            "report_date": str(date.today()),
            "summary": "Colisión por alcance en semáforo",
        },
        headers=_headers(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["officer_name"] == "Oficial Perez"
    assert data["report_code"] == "ACT-2026-001"


@pytest.mark.asyncio
async def test_update_traffic_report(async_client, user_admin):
    token = await _login(async_client)
    ph_id = await _create_policyholder(async_client, token, "TRU")
    pol_id = await _create_policy(async_client, token, ph_id, "TRU")
    veh_id = await _create_vehicle(async_client, token, pol_id, "TRU")
    claim = await _create_claim(async_client, token, ph_id, pol_id, veh_id, "TRU")

    create_resp = await async_client.post(
        "/api/traffic-reports?claim_id=" + claim["id"],
        json={"officer_name": "Original"},
        headers=_headers(token),
    )
    report_id = create_resp.json()["id"]

    resp = await async_client.put(
        f"/api/traffic-reports/{report_id}",
        json={"officer_name": "Actualizado"},
        headers=_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json()["officer_name"] == "Actualizado"


@pytest.mark.asyncio
async def test_delete_traffic_report(async_client, user_admin):
    token = await _login(async_client)
    ph_id = await _create_policyholder(async_client, token, "TRD")
    pol_id = await _create_policy(async_client, token, ph_id, "TRD")
    veh_id = await _create_vehicle(async_client, token, pol_id, "TRD")
    claim = await _create_claim(async_client, token, ph_id, pol_id, veh_id, "TRD")

    create_resp = await async_client.post(
        "/api/traffic-reports?claim_id=" + claim["id"],
        json={"officer_name": "Para borrar"},
        headers=_headers(token),
    )
    report_id = create_resp.json()["id"]

    resp = await async_client.delete(
        f"/api/traffic-reports/{report_id}",
        headers=_headers(token),
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_create_traffic_report_claim_not_found(async_client, user_admin):
    token = await _login(async_client)
    resp = await async_client.post(
        "/api/traffic-reports?claim_id=00000000-0000-0000-0000-000000000099",
        json={"officer_name": "Nadie"},
        headers=_headers(token),
    )
    assert resp.status_code == 404


# ── Evidence listing ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_claim_evidences_empty(async_client, user_admin):
    token = await _login(async_client)
    ph_id = await _create_policyholder(async_client, token, "EL")
    pol_id = await _create_policy(async_client, token, ph_id, "EL")
    veh_id = await _create_vehicle(async_client, token, pol_id, "EL")
    claim = await _create_claim(async_client, token, ph_id, pol_id, veh_id, "EL")

    resp = await async_client.get(
        f"/api/evidences/claims/{claim['id']}",
        headers=_headers(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []
