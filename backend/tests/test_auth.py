"""Auth endpoint tests — 11 scenarios covering the full auth flow."""

import pyotp
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant
from app.models.user import User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _login_headers(tenant_slug: str) -> dict:
    return {"X-Tenant-Slug": tenant_slug}


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


async def test_register_success(
    async_client: AsyncClient, tenant_a: Tenant
) -> None:
    """POST /api/auth/register with a valid tenant slug returns 201 and tokens."""
    response = await async_client.post(
        "/api/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "Password123!",
            "full_name": "New User",
            "tenant_slug": tenant_a.slug,
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "newuser@example.com"


async def test_register_duplicate_email(
    async_client: AsyncClient, user_admin: User, tenant_a: Tenant
) -> None:
    """Registering the same email twice in the same tenant returns 409."""
    response = await async_client.post(
        "/api/auth/register",
        json={
            "email": user_admin.email,
            "password": "Password123!",
            "full_name": "Duplicate User",
            "tenant_slug": tenant_a.slug,
        },
    )
    assert response.status_code == 409


async def test_register_invalid_tenant(async_client: AsyncClient) -> None:
    """Registration with a non-existent tenant slug returns 404."""
    response = await async_client.post(
        "/api/auth/register",
        json={
            "email": "someone@example.com",
            "password": "Password123!",
            "full_name": "Someone",
            "tenant_slug": "does-not-exist",
        },
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


async def test_login_success(
    async_client: AsyncClient, user_admin: User, tenant_a: Tenant
) -> None:
    """Valid credentials return 200 with access_token and refresh_token."""
    response = await async_client.post(
        "/api/auth/login",
        json={"email": user_admin.email, "password": "Password123!"},
        headers=_login_headers(tenant_a.slug),
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body


async def test_login_wrong_password(
    async_client: AsyncClient, user_admin: User, tenant_a: Tenant
) -> None:
    """Wrong password returns 401."""
    response = await async_client.post(
        "/api/auth/login",
        json={"email": user_admin.email, "password": "WrongPassword!"},
        headers=_login_headers(tenant_a.slug),
    )
    assert response.status_code == 401


async def test_login_inactive_user(
    async_client: AsyncClient,
    db_session: AsyncSession,
    user_admin: User,
    tenant_a: Tenant,
) -> None:
    """An inactive account returns 401 even with correct credentials."""
    user_admin.is_active = False
    db_session.add(user_admin)
    await db_session.commit()

    response = await async_client.post(
        "/api/auth/login",
        json={"email": user_admin.email, "password": "Password123!"},
        headers=_login_headers(tenant_a.slug),
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Refresh token rotation
# ---------------------------------------------------------------------------


async def test_refresh_token_success(
    async_client: AsyncClient, user_admin: User, tenant_a: Tenant
) -> None:
    """A valid refresh token returns a new access_token."""
    login = await async_client.post(
        "/api/auth/login",
        json={"email": user_admin.email, "password": "Password123!"},
        headers=_login_headers(tenant_a.slug),
    )
    refresh_token = login.json()["refresh_token"]

    response = await async_client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


async def test_refresh_token_revoked(
    async_client: AsyncClient, user_admin: User, tenant_a: Tenant
) -> None:
    """Using an already-rotated refresh token returns 401."""
    login = await async_client.post(
        "/api/auth/login",
        json={"email": user_admin.email, "password": "Password123!"},
        headers=_login_headers(tenant_a.slug),
    )
    refresh_token = login.json()["refresh_token"]

    # First rotation — should succeed and revoke the token
    first = await async_client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert first.status_code == 200

    # Second use of the same token — must be rejected
    second = await async_client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert second.status_code == 401


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------


async def test_logout_revokes_token(
    async_client: AsyncClient, user_admin: User, tenant_a: Tenant
) -> None:
    """After logout the same refresh token cannot be used again."""
    login = await async_client.post(
        "/api/auth/login",
        json={"email": user_admin.email, "password": "Password123!"},
        headers=_login_headers(tenant_a.slug),
    )
    refresh_token = login.json()["refresh_token"]

    logout = await async_client.post(
        "/api/auth/logout",
        json={"refresh_token": refresh_token},
    )
    assert logout.status_code == 200
    assert logout.json()["message"] == "ok"

    refresh = await async_client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh.status_code == 401


# ---------------------------------------------------------------------------
# MFA
# ---------------------------------------------------------------------------


async def test_mfa_setup_and_verify(
    async_client: AsyncClient, user_admin: User, tenant_a: Tenant
) -> None:
    """MFA setup returns secret + qr_uri; verify activates MFA on the account."""
    # Obtain a valid access token
    login = await async_client.post(
        "/api/auth/login",
        json={"email": user_admin.email, "password": "Password123!"},
        headers=_login_headers(tenant_a.slug),
    )
    access_token = login.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {access_token}"}

    # Setup — should return secret and qr_uri
    setup = await async_client.post("/api/auth/mfa/setup", headers=auth_headers)
    assert setup.status_code == 200
    setup_body = setup.json()
    assert "secret" in setup_body
    # qr_uri debe ser una imagen PNG embebida (data URI), lista para <img src>,
    # no el otpauth:// crudo (que el navegador no puede renderizar como imagen).
    assert setup_body["qr_uri"].startswith("data:image/png;base64,")

    # Verify with a real TOTP code generated from the returned secret
    totp = pyotp.TOTP(setup_body["secret"])
    code = totp.now()

    verify = await async_client.post(
        "/api/auth/mfa/verify",
        json={"code": code},
        headers=auth_headers,
    )
    assert verify.status_code == 200
    assert verify.json()["message"] == "MFA activado"


async def test_login_with_mfa_enabled_requires_code(
    async_client: AsyncClient, user_admin: User, tenant_a: Tenant
) -> None:
    """DT-24: con MFA activo, el login SIN código devuelve 200 {mfa_required:true}
    (no 500), y CON código válido devuelve los tokens."""
    headers = _login_headers(tenant_a.slug)

    # Activar MFA primero
    login = await async_client.post(
        "/api/auth/login",
        json={"email": user_admin.email, "password": "Password123!"},
        headers=headers,
    )
    access_token = login.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {access_token}"}
    setup = await async_client.post("/api/auth/mfa/setup", headers=auth_headers)
    secret = setup.json()["secret"]
    totp = pyotp.TOTP(secret)
    await async_client.post(
        "/api/auth/mfa/verify", json={"code": totp.now()}, headers=auth_headers
    )

    # Login SIN código → 200 con mfa_required (antes daba 500)
    no_code = await async_client.post(
        "/api/auth/login",
        json={"email": user_admin.email, "password": "Password123!"},
        headers=headers,
    )
    assert no_code.status_code == 200, no_code.text
    assert no_code.json() == {"mfa_required": True}

    # Login CON código → tokens
    with_code = await async_client.post(
        "/api/auth/login",
        json={
            "email": user_admin.email,
            "password": "Password123!",
            "mfa_code": totp.now(),
        },
        headers=headers,
    )
    assert with_code.status_code == 200, with_code.text
    assert "access_token" in with_code.json()


# ---------------------------------------------------------------------------
# Cross-tenant isolation
# ---------------------------------------------------------------------------


async def test_cross_tenant_isolation(
    async_client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Tenant,
    tenant_b: Tenant,
) -> None:
    """A user registered in tenant_a cannot log in via tenant_b's slug."""
    shared_email = "shared@example.com"
    shared_password = "Password123!"

    # Register the same email in both tenants (allowed — different tenants)
    await async_client.post(
        "/api/auth/register",
        json={
            "email": shared_email,
            "password": shared_password,
            "full_name": "User A",
            "tenant_slug": tenant_a.slug,
        },
    )
    await async_client.post(
        "/api/auth/register",
        json={
            "email": shared_email,
            "password": shared_password,
            "full_name": "User B",
            "tenant_slug": tenant_b.slug,
        },
    )

    # Login with tenant_a header — must succeed
    login_a = await async_client.post(
        "/api/auth/login",
        json={"email": shared_email, "password": shared_password},
        headers=_login_headers(tenant_a.slug),
    )
    assert login_a.status_code == 200
    tenant_id_a = login_a.json()["user"]["tenant_id"]

    # Login with tenant_b header — must succeed but return a different tenant_id
    login_b = await async_client.post(
        "/api/auth/login",
        json={"email": shared_email, "password": shared_password},
        headers=_login_headers(tenant_b.slug),
    )
    assert login_b.status_code == 200
    tenant_id_b = login_b.json()["user"]["tenant_id"]

    # The two tenant IDs must be different, proving isolation
    assert tenant_id_a != tenant_id_b
    assert str(tenant_a.id) == tenant_id_a
    assert str(tenant_b.id) == tenant_id_b
