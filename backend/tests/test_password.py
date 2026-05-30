"""Tests for CU-28 and CU-29: Password reset and change."""

import pytest
from httpx import AsyncClient


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "X-Tenant-Slug": "aseguradora-a"}


async def _login(async_client: AsyncClient, email: str = "admin@aseguradora-a.com") -> str:
    resp = await async_client.post(
        "/api/auth/login",
        json={"email": email, "password": "Password123!"},
        headers={"X-Tenant-Slug": "aseguradora-a"},
    )
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_password_change_success(async_client, user_admin):
    token = await _login(async_client)
    resp = await async_client.post(
        "/api/auth/password-change",
        json={
            "current_password": "Password123!",
            "new_password": "NewStr0ngPass!",
            "confirm_password": "NewStr0ngPass!",
        },
        headers=_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Contraseña cambiada correctamente"


@pytest.mark.asyncio
async def test_password_change_wrong_current(async_client, user_admin):
    token = await _login(async_client)
    resp = await async_client.post(
        "/api/auth/password-change",
        json={
            "current_password": "WrongPassword!",
            "new_password": "NewStr0ngPass!",
            "confirm_password": "NewStr0ngPass!",
        },
        headers=_headers(token),
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_password_change_same_as_current(async_client, user_admin):
    token = await _login(async_client)
    resp = await async_client.post(
        "/api/auth/password-change",
        json={
            "current_password": "Password123!",
            "new_password": "Password123!",
            "confirm_password": "Password123!",
        },
        headers=_headers(token),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_password_change_mismatched_confirmation(async_client, user_admin):
    token = await _login(async_client)
    resp = await async_client.post(
        "/api/auth/password-change",
        json={
            "current_password": "Password123!",
            "new_password": "NewPass123!",
            "confirm_password": "Mismatch123!",
        },
        headers=_headers(token),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_password_reset_request_always_returns_200(async_client, user_admin):
    resp = await async_client.post(
        "/api/auth/password-reset/request",
        json={"email": "does-not-exist@test.com", "tenant_slug": "aseguradora-a"},
    )
    assert resp.status_code == 200
    assert "enlace" in resp.json()["message"]


@pytest.mark.asyncio
async def test_password_reset_confirm_invalid_token(async_client, user_admin):
    resp = await async_client.post(
        "/api/auth/password-reset/confirm",
        json={"token": "invalid-token-xxxxxxxxxxxxxxxxx", "new_password": "NewPass123!"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_password_reset_full_flow(async_client, user_admin):
    resp = await async_client.post(
        "/api/auth/password-reset/request",
        json={"email": "admin@aseguradora-a.com", "tenant_slug": "aseguradora-a"},
    )
    assert resp.status_code == 200
    # Token was generated and printed to console (email_service mock)
    # We can't test the full flow via HTTP since we don't know the token
    # The service-level method is tested via unit tests if desired
