"""Application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import settings
from app.middleware.tenant import TenantMiddleware
from app.routers import auth, users, policyholders, policies, vehicles, claim_requests, claims
from app.routers import evidences, document_requests, traffic_reports

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Best-effort: create the evidence bucket and apply CORS rules on startup so
    # a fresh clone works without manual bootstrap. If S3 (or LocalStack) is
    # unreachable we log and continue — the app still serves non-S3 endpoints.
    try:
        from app.services.storage_service import storage_service
        await storage_service.ensure_bucket()
        logger.info("S3 bucket %s ready", settings.AWS_S3_BUCKET)
    except Exception as e:
        logger.warning("Could not ensure S3 bucket on startup (%s). Evidence uploads will fail until storage is reachable.", e)
    yield


app = FastAPI(
    title="Gestión Siniestros API",
    version="1.0.0",
    description="Backend multi-tenant para gestión de siniestros de seguros.",
    lifespan=lifespan,
)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Multi-tenant resolution (DT-01) — added FIRST so it sits inside CORS.
app.add_middleware(TenantMiddleware)

# CORS — added LAST so it becomes the outermost wrapper and still adds
# headers on 4xx/5xx responses (Starlette wraps in reverse-registration order).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(policyholders.router, prefix="/api")
app.include_router(policies.router, prefix="/api")
app.include_router(vehicles.router, prefix="/api")
app.include_router(claim_requests.router, prefix="/api")
app.include_router(claims.router, prefix="/api")
app.include_router(evidences.router, prefix="/api")
app.include_router(document_requests.router, prefix="/api")
app.include_router(traffic_reports.router, prefix="/api")


@app.get("/health", tags=["ops"])
async def health() -> dict:
    """Liveness probe endpoint."""
    return {"status": "ok"}
