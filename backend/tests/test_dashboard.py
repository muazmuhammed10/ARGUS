"""ARGUS — Dashboard endpoint tests."""

import pytest
from httpx import AsyncClient
from tests.conftest import get_auth_token

pytestmark = pytest.mark.asyncio


class TestDashboard:
    async def test_summary_returns_real_counts(self, client: AsyncClient, admin_user):
        token = await get_auth_token(client, "admin@example.com", "TestAdmin@123!")
        resp = await client.get(
            "/api/v1/dashboard/summary",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        # All fields present
        assert "total_events" in data
        assert "critical_events" in data
        assert "high_events" in data
        assert "open_incidents" in data
        assert "resolved_incidents" in data
        assert "open_alerts" in data
        assert "unique_source_ips" in data
        assert "total_assets" in data
        # All values are non-negative integers
        for key in ["total_events", "critical_events", "open_incidents", "open_alerts"]:
            assert data[key] >= 0

    async def test_summary_requires_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/dashboard/summary")
        assert resp.status_code == 401

    async def test_trends_returns_structure(self, client: AsyncClient, admin_user):
        token = await get_auth_token(client, "admin@example.com", "TestAdmin@123!")
        resp = await client.get(
            "/api/v1/dashboard/trends?days=7",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "trend_data" in data
        assert "event_type_distribution" in data
        assert isinstance(data["trend_data"], list)

    async def test_recent_alerts_endpoint(self, client: AsyncClient, admin_user):
        token = await get_auth_token(client, "admin@example.com", "TestAdmin@123!")
        resp = await client.get(
            "/api/v1/dashboard/alerts/recent",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        assert "items" in resp.json()

    async def test_viewer_can_see_dashboard(self, client: AsyncClient, viewer_user):
        token = await get_auth_token(client, "viewer@example.com", "TestViewer@123!")
        resp = await client.get(
            "/api/v1/dashboard/summary",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200

    async def test_summary_reflects_ingested_event(self, client: AsyncClient, analyst_user):
        """After ingesting a CRITICAL event, total_events should increase."""
        token = await get_auth_token(client, "analyst@example.com", "TestAnalyst@123!")

        # Get baseline
        before = await client.get(
            "/api/v1/dashboard/summary",
            headers={"Authorization": f"Bearer {token}"}
        )
        before_total = before.json()["total_events"]

        # Ingest an event
        await client.post(
            "/api/v1/events/ingest",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "source_system": "dashboard-test",
                "event_type": "AUTHENTICATION",
                "severity": "CRITICAL",
                "description": "Dashboard test event",
                "is_synthetic": True,
            }
        )

        # Get updated summary
        after = await client.get(
            "/api/v1/dashboard/summary",
            headers={"Authorization": f"Bearer {token}"}
        )
        after_total = after.json()["total_events"]
        assert after_total == before_total + 1
