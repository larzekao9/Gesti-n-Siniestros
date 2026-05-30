"""Tests for CU-23: User management (admin CRUD)."""

import pytest
from httpx import AsyncClient

from app.models.user import Role, User
from app.core.security import hash_password


def _auth_headers(access_token: str) -> dict:
    return {"Authorization": f"Bearer {access_token}", "X-Tenant-Slug": "aseguradora-a"}


async def _login_as_admin(async_client: AsyncClient) -> str:
    resp = await async_client.post(
        "/api/auth/login",
        json={"email": "admin@aseguradora-a.com", "password": "Password123!"},
        headers={"X-Tenant-Slug": "aseguradora-a"},
    )
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_list_users_empty(async_client, user_admin):
    token = await _login_as_admin(async_client)
    resp = await async_client.get("/api/users", headers=_auth_headers(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1  # at least the admin


@pytest.mark.asyncio
async def test_create_user_success(async_client, user_admin):
    token = await _login_as_admin(async_client)
    resp = await async_client.post(
        "/api/users",
        json={
            "email": "analyst@test.com",
            "password": "Password123!",
            "full_name": "Test Analyst",
            "role": "analyst",
        },
        headers=_auth_headers(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "analyst@test.com"
    assert data["role"] == "analyst"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_create_user_duplicate_email(async_client, user_admin):
    token = await _login_as_admin(async_client)
    await async_client.post(
        "/api/users",
        json={
            "email": "dup@test.com",
            "password": "Password123!",
            "full_name": "First",
            "role": "analyst",
        },
        headers=_auth_headers(token),
    )
    resp = await async_client.post(
        "/api/users",
        json={
            "email": "dup@test.com",
            "password": "Password123!",
            "full_name": "Second",
            "role": "supervisor",
        },
        headers=_auth_headers(token),
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_update_user(async_client, user_admin):
    token = await _login_as_admin(async_client)
    create_resp = await async_client.post(
        "/api/users",
        json={
            "email": "to-update@test.com",
            "password": "Password123!",
            "full_name": "Original",
            "role": "analyst",
        },
        headers=_auth_headers(token),
    )
    user_id = create_resp.json()["id"]

    resp = await async_client.patch(
        f"/api/users/{user_id}",
        json={"full_name": "Updated", "role": "supervisor"},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Updated"
    assert resp.json()["role"] == "supervisor"


@pytest.mark.asyncio
async def test_cannot_deactivate_last_admin(async_client, user_admin):
    token = await _login_as_admin(async_client)
    resp = await async_client.patch(
        f"/api/users/{user_admin.id}",
        json={"is_active": False},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_non_admin_cannot_create_user(async_client, user_admin):
    token = await _login_as_admin(async_client)
    create_resp = await async_client.post(
        "/api/users",
        json={
            "email": "analyst@noadmin.com",
            "password": "Password123!",
            "full_name": "No Admin",
            "role": "analyst",
        },
        headers=_auth_headers(token),
    )
    analyst_id = create_resp.json()["id"]

    resp = await async_client.patch(
        f"/api/users/{analyst_id}",
        json={"password": "NewPass123!"},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200

    analyst_login = await async_client.post(
        "/api/auth/login",
        json={"email": "analyst@noadmin.com", "password": "NewPass123!"},
        headers={"X-Tenant-Slug": "aseguradora-a"},
    )
    analyst_token = analyst_login.json()["access_token"]

    resp = await async_client.post(
        "/api/users",
        json={
            "email": "hacker@test.com",
            "password": "Password123!",
            "full_name": "Hacker",
            "role": "admin",
        },
        headers=_auth_headers(analyst_token),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_get_user_by_id(async_client, user_admin):
    token = await _login_as_admin(async_client)
    resp = await async_client.get(
        f"/api/users/{user_admin.id}", headers=_auth_headers(token)
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "admin@aseguradora-a.com"
