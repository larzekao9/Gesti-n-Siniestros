"""Tests for CU-13: Vehicle CRUD."""

from datetime import date, timedelta

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


async def _setup_policy(async_client: AsyncClient, token: str) -> str:
    ph_resp = await async_client.post(
        "/api/policyholders",
        json={"document_id": "VEH-PH", "full_name": "Vehicle Owner", "phone": "3000000"},
        headers=_headers(token),
    )
    ph_id = ph_resp.json()["id"]
    today = date.today()
    pol_resp = await async_client.post(
        "/api/policies",
        json={
            "policy_number": "VEH-POL",
            "policyholder_id": ph_id,
            "valid_from": str(today),
            "valid_to": str(today + timedelta(days=365)),
            "coverage_type": "full",
        },
        headers=_headers(token),
    )
    return pol_resp.json()["id"]


@pytest.mark.asyncio
async def test_create_vehicle_success(async_client, user_admin):
    token = await _login(async_client)
    policy_id = await _setup_policy(async_client, token)

    resp = await async_client.post(
        "/api/vehicles",
        json={
            "plate": "ABC123",
            "make": "Toyota",
            "model": "Corolla",
            "year": 2020,
            "policy_id": policy_id,
        },
        headers=_headers(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["plate"] == "ABC123"
    assert data["make"] == "Toyota"


@pytest.mark.asyncio
async def test_create_vehicle_duplicate_plate(async_client, user_admin):
    token = await _login(async_client)
    policy_id = await _setup_policy(async_client, token)

    payload = {
        "plate": "DUP-PLATE",
        "make": "Honda",
        "model": "Civic",
        "year": 2021,
        "policy_id": policy_id,
    }
    await async_client.post("/api/vehicles", json=payload, headers=_headers(token))
    resp = await async_client.post("/api/vehicles", json=payload, headers=_headers(token))
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_create_vehicle_nonexistent_policy(async_client, user_admin):
    token = await _login(async_client)
    resp = await async_client.post(
        "/api/vehicles",
        json={
            "plate": "ZZZ999",
            "make": "Ford",
            "model": "Focus",
            "year": 2019,
            "policy_id": "00000000-0000-0000-0000-000000000000",
        },
        headers=_headers(token),
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_vehicles(async_client, user_admin):
    token = await _login(async_client)
    policy_id = await _setup_policy(async_client, token)

    for i, plate in enumerate(["CAR1", "CAR2", "CAR3"]):
        await async_client.post(
            "/api/vehicles",
            json={"plate": plate, "make": "M", "model": "X", "year": 2020 + i, "policy_id": policy_id},
            headers=_headers(token),
        )
    resp = await async_client.get("/api/vehicles", headers=_headers(token))
    assert resp.status_code == 200
    assert resp.json()["total"] == 3
