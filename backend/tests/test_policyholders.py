"""Tests for CU-11: Policyholder CRUD."""

import pytest
from httpx import AsyncClient


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "X-Tenant-Slug": "aseguradora-a"}


async def _login(async_client: AsyncClient) -> str:
    resp = await async_client.post(
        "/api/auth/login",
        json={"email": "admin@aseguradora-a.com", "password": "Password123!"},
        headers={"X-Tenant-Slug": "aseguradora-a"},
    )
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_create_policyholder_success(async_client, user_admin):
    token = await _login(async_client)
    resp = await async_client.post(
        "/api/policyholders",
        json={
            "document_id": "123456789",
            "full_name": "Juan Perez",
            "phone": "3001234567",
            "email": "juan@example.com",
            "address": "Calle 123",
        },
        headers=_headers(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["full_name"] == "Juan Perez"
    assert data["document_id"] == "123456789"


@pytest.mark.asyncio
async def test_create_duplicate_document_id(async_client, user_admin):
    token = await _login(async_client)
    payload = {
        "document_id": "DUP123",
        "full_name": "AA",
        "phone": "3000000000",
    }
    await async_client.post("/api/policyholders", json=payload, headers=_headers(token))
    resp = await async_client.post("/api/policyholders", json=payload, headers=_headers(token))
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_list_policyholders(async_client, user_admin):
    token = await _login(async_client)
    for i in range(3):
        await async_client.post(
            "/api/policyholders",
            json={
                "document_id": f"DOC{i}",
                "full_name": f"Person {i}",
                "phone": f"300000000{i}",
            },
            headers=_headers(token),
        )
    resp = await async_client.get("/api/policyholders?limit=10", headers=_headers(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3


@pytest.mark.asyncio
async def test_search_policyholders(async_client, user_admin):
    token = await _login(async_client)
    await async_client.post(
        "/api/policyholders",
        json={"document_id": "SRC100", "full_name": "Carlos Search", "phone": "30011100"},
        headers=_headers(token),
    )
    await async_client.post(
        "/api/policyholders",
        json={"document_id": "SRC200", "full_name": "Maria Other", "phone": "30022200"},
        headers=_headers(token),
    )
    resp = await async_client.get(
        "/api/policyholders?search=Carlos", headers=_headers(token)
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert "Carlos" in data["items"][0]["full_name"]


@pytest.mark.asyncio
async def test_update_policyholder(async_client, user_admin):
    token = await _login(async_client)
    create = await async_client.post(
        "/api/policyholders",
        json={"document_id": "UPD001", "full_name": "Old Name", "phone": "3000000"},
        headers=_headers(token),
    )
    ph_id = create.json()["id"]

    resp = await async_client.patch(
        f"/api/policyholders/{ph_id}",
        json={"full_name": "New Name", "status": "inactive"},
        headers=_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "New Name"
    assert resp.json()["status"] == "inactive"
