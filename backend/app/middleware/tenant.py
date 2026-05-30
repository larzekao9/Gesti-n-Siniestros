"""Tenant resolution middleware.

Reads the ``X-Tenant-Slug`` request header and attaches the resolved
``Tenant`` instance (or ``None``) to ``request.state.tenant``.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.tenant import Tenant


class TenantMiddleware(BaseHTTPMiddleware):
    """Resolves the tenant from ``X-Tenant-Slug`` and stores it on request state."""

    async def dispatch(self, request: Request, call_next) -> Response:
        slug = request.headers.get("X-Tenant-Slug")
        request.state.tenant = None

        if slug:
            # Use test-overridden session factory if available via app.state
            SessionFactory = getattr(
                request.app.state, "_middleware_session_factory", AsyncSessionLocal
            )
            async with SessionFactory() as db:
                result = await db.execute(
                    select(Tenant).where(Tenant.slug == slug, Tenant.is_active.is_(True))
                )
                request.state.tenant = result.scalar_one_or_none()

        return await call_next(request)
