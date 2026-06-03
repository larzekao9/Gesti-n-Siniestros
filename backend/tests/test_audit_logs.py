"""Tests for CU-31: audit log traceability views (read-only)."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.tenant import Tenant
from app.models.user import User

HEADERS = {"X-Tenant-Slug": "aseguradora-a"}


async def _login(async_client: AsyncClient, email: str) -> str:
    resp = await async_client.post(
        "/api/auth/login",
        json={"email": email, "password": "Password123!"},
        headers=HEADERS,
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", **HEADERS}


def _log(tenant: Tenant, action: str, *, actor: User | None = None,
         entity_type: str = "claim", entity_id=None) -> AuditLog:
    return AuditLog(
        tenant_id=tenant.id,
        actor_user_id=actor.id if actor else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
    )


@pytest.mark.asyncio
async def test_admin_global_view_sees_all(async_client, db_session, tenant_a, user_admin, user_analyst):
    db_session.add(_log(tenant_a, "CREATE_CLAIM", actor=user_analyst))
    db_session.add(_log(tenant_a, "LOGIN", actor=user_admin, entity_type="user"))
    await db_session.commit()

    token = await _login(async_client, "admin@aseguradora-a.com")
    resp = await async_client.get("/api/audit-logs", headers=_auth(token))
    assert resp.status_code == 200, resp.text
    actions = {i["action"] for i in resp.json()["items"]}
    assert "CREATE_CLAIM" in actions
    assert "LOGIN" in actions  # admin ve eventos sensibles


@pytest.mark.asyncio
async def test_supervisor_hides_sensitive(async_client, db_session, tenant_a, user_admin, user_supervisor):
    db_session.add(_log(tenant_a, "CREATE_CLAIM", actor=user_supervisor))
    db_session.add(_log(tenant_a, "PASSWORD_RESET", actor=user_admin, entity_type="user"))
    await db_session.commit()

    token = await _login(async_client, "supervisor@aseguradora-a.com")
    resp = await async_client.get("/api/audit-logs", headers=_auth(token))
    assert resp.status_code == 200
    actions = {i["action"] for i in resp.json()["items"]}
    assert "CREATE_CLAIM" in actions
    assert "PASSWORD_RESET" not in actions  # sensible, oculto al supervisor


@pytest.mark.asyncio
async def test_analyst_sees_only_own_activity(async_client, db_session, tenant_a, user_admin, user_analyst):
    db_session.add(_log(tenant_a, "CREATE_OBSERVATION", actor=user_analyst))
    db_session.add(_log(tenant_a, "DECIDE", actor=user_admin))
    await db_session.commit()

    token = await _login(async_client, "analyst@aseguradora-a.com")
    resp = await async_client.get("/api/audit-logs", headers=_auth(token))
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert all(i["actor_user_id"] == str(user_analyst.id) for i in items)
    actions = {i["action"] for i in items}
    assert "CREATE_OBSERVATION" in actions
    assert "DECIDE" not in actions


@pytest.mark.asyncio
async def test_entity_view_filters_by_entity(async_client, db_session, tenant_a, user_admin):
    claim_id = uuid4()
    other_id = uuid4()
    db_session.add(_log(tenant_a, "STATE_CHANGE", actor=user_admin, entity_id=claim_id))
    db_session.add(_log(tenant_a, "CREATE_CLAIM", actor=user_admin, entity_id=other_id))
    await db_session.commit()

    token = await _login(async_client, "admin@aseguradora-a.com")
    resp = await async_client.get(
        f"/api/audit-logs?entity_type=claim&entity_id={claim_id}", headers=_auth(token)
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["action"] == "STATE_CHANGE"


@pytest.mark.asyncio
async def test_multitenant_isolation(async_client, db_session, tenant_a, tenant_b, user_admin):
    db_session.add(_log(tenant_b, "CREATE_CLAIM"))
    db_session.add(_log(tenant_a, "DECIDE", actor=user_admin))
    await db_session.commit()

    token = await _login(async_client, "admin@aseguradora-a.com")
    resp = await async_client.get("/api/audit-logs", headers=_auth(token))
    assert resp.status_code == 200
    actions = {i["action"] for i in resp.json()["items"]}
    assert actions == {"DECIDE"}
