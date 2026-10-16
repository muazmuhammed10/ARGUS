"""
ARGUS — Main FastAPI application entry point.
"""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import engine, Base
from app.core.logging import configure_logging

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    configure_logging()
    log.info("ARGUS starting up", version=settings.APP_VERSION, env=settings.APP_ENV)

    # Create database tables if they don't exist
    # In production, use: alembic upgrade head
    # In development, we create them directly for convenience
    # In test mode, the conftest.py manages its own engine/tables
    if settings.APP_ENV not in ("test",):
        async with engine.begin() as conn:
            if settings.APP_ENV == "development":
                await conn.run_sync(
                    lambda sync_conn: Base.metadata.create_all(sync_conn, checkfirst=True)
                )
                log.info("Database tables verified")

    yield

    log.info("ARGUS shutting down")
    await engine.dispose()


# Rate limiter — keyed by remote IP
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="ARGUS Threat Intelligence Platform",
    description=(
        "AI-Powered Threat Intelligence & Cyber Defense Platform. "
        "Provides security event monitoring, detection, incident management, "
        "and AI-assisted analysis for security operations teams."
    ),
    version=settings.APP_VERSION,
    docs_url="/api/docs" if settings.APP_ENV != "production" else None,
    redoc_url="/api/redoc" if settings.APP_ENV != "production" else None,
    openapi_url="/api/openapi.json" if settings.APP_ENV != "production" else None,
    lifespan=lifespan,
)

# Attach rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — restrict to configured origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)

# Include versioned API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for Docker and load balancers."""
    return {
        "status": "healthy",
        "service": "argus-backend",
        "version": settings.APP_VERSION,
    }
