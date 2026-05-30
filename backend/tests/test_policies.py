"""Tests for CU-12: Policy CRUD."""

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


async def _create_policyholder(async_client: AsyncClient, token: str) -> str:
    resp = await async_client.post(
        "/api/policyholders",
        json={"document_id": "PH-POL-001", "full_name": "Policy Holder", "phone": "3000000"},
        headers=_headers(token),
    )
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_create_policy_success(async_client, user_admin):
    token = await _login(async_client)
    ph_id = await _create_policyholder(async_client, token)

    today = date.today()
    resp = await async_client.post(
        "/api/policies",
        json={
            "policy_number": "POL-0001",
            "policyholder_id": ph_id,
            "valid_from": str(today),
            "valid_to": str(today + timedelta(days=365)),
            "coverage_type": "full",
        },
        headers=_headers(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["policy_number"] == "POL-0001"
    assert data["coverage_type"] == "full"


@pytest.mark.asyncio
async def test_create_policy_invalid_dates(async_client, user_admin):
    token = await _login(async_client)
    ph_id = await _create_policyholder(async_client, token)

    today = date.today()
    resp = await async_client.post(
        "/api/policies",
        json={
            "policy_number": "POL-BAD",
            "policyholder_id": ph_id,
            "valid_from": str(today + timedelta(days=10)),
            "valid_to": str(today),
            "coverage_type": "basic",
        },
        headers=_headers(token),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_policy_duplicate_number(async_client, user_admin):
    token = await _login(async_client)
    ph_id = await _create_policyholder(async_client, token)

    today = date.today()
    payload = {
        "policy_number": "POL-DUP",
        "policyholder_id": ph_id,
        "valid_from": str(today),
        "valid_to": str(today + timedelta(days=365)),
        "coverage_type": "full",
    }
    await async_client.post("/api/policies", json=payload, headers=_headers(token))
    resp = await async_client.post("/api/policies", json=payload, headers=_headers(token))
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_list_policies(async_client, user_admin):
    token = await _login(async_client)
    ph_id = await _create_policyholder(async_client, token)

    today = date.today()
    for i in range(2):
        await async_client.post(
            "/api/policies",
            json={
                "policy_number": f"POL-L{i}",
                "policyholder_id": ph_id,
                "valid_from": str(today),
                "valid_to": str(today + timedelta(days=365)),
                "coverage_type": "basic",
            },
            headers=_headers(token),
        )
    resp = await async_client.get("/api/policies", headers=_headers(token))
    assert resp.status_code == 200
    assert resp.json()["total"] == 2
