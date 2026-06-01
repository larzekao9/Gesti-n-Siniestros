"""Application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import settings
from app.middleware.tenant import TenantMiddleware
from app.routers import auth, users, policyholders, policies, vehicles, claim_requests, claims

app = FastAPI(
    title="Gestión Siniestros API",
    version="1.0.0",
    description="Backend multi-tenant para gestión de siniestros de seguros.",
)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Multi-tenant resolution (DT-01)
app.add_middleware(TenantMiddleware)

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(policyholders.router, prefix="/api")
app.include_router(policies.router, prefix="/api")
app.include_router(vehicles.router, prefix="/api")
app.include_router(claim_requests.router, prefix="/api")
app.include_router(claims.router, prefix="/api")


@app.get("/health", tags=["ops"])
async def health() -> dict:
    """Liveness probe endpoint."""
    return {"status": "ok"}
