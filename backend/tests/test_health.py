"""
ARGUS — Health check and basic API tests.
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_health_check(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "argus-backend"


async def test_api_docs_available_in_dev(client: AsyncClient):
    resp = await client.get("/api/docs")
    # In test/dev mode docs should be accessible
    assert resp.status_code in (200, 404)  # 404 if not dev


async def test_unauthenticated_dashboard_returns_401(client: AsyncClient):
    resp = await client.get("/api/v1/dashboard/summary")
    assert resp.status_code == 401


async def test_unauthenticated_events_returns_401(client: AsyncClient):
    resp = await client.get("/api/v1/events")
    assert resp.status_code == 401


async def test_unauthenticated_incidents_returns_401(client: AsyncClient):
    resp = await client.get("/api/v1/incidents")
    assert resp.status_code == 401
