"""
ARGUS — Security event ingestion and query tests.
"""

import pytest
from datetime import datetime, timezone
from httpx import AsyncClient

from tests.conftest import get_auth_token

pytestmark = pytest.mark.asyncio


class TestEventIngestion:
    async def test_ingest_single_event(self, client: AsyncClient, analyst_user):
        token = await get_auth_token(client, "analyst@example.com", "TestAnalyst@123!")
        resp = await client.post(
            "/api/v1/events/ingest",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "source_system": "test-system",
                "event_type": "AUTHENTICATION",
                "severity": "HIGH",
                "source_ip": "192.0.2.1",
                "username": "testuser",
                "hostname": "test-host",
                "description": "Test failed authentication attempt",
                "is_synthetic": True,
            }
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["source_system"] == "test-system"
        assert data["event_type"] == "AUTHENTICATION"
        assert data["severity"] == "HIGH"
        assert data["is_synthetic"] is True

    async def test_ingest_requires_auth(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/events/ingest",
            json={"source_system": "x", "event_type": "AUTHENTICATION", "severity": "LOW",
                  "description": "test"}
        )
        assert resp.status_code == 401

    async def test_viewer_cannot_ingest(self, client: AsyncClient, viewer_user):
        token = await get_auth_token(client, "viewer@example.com", "TestViewer@123!")
        resp = await client.post(
            "/api/v1/events/ingest",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "source_system": "test",
                "event_type": "AUTHENTICATION",
                "severity": "LOW",
                "description": "Test event",
            }
        )
        assert resp.status_code == 403

    async def test_ingest_invalid_event_type(self, client: AsyncClient, analyst_user):
        token = await get_auth_token(client, "analyst@example.com", "TestAnalyst@123!")
        resp = await client.post(
            "/api/v1/events/ingest",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "source_system": "test",
                "event_type": "INVALID_TYPE",
                "severity": "LOW",
                "description": "Test",
            }
        )
        assert resp.status_code == 422

    async def test_ingest_invalid_ip(self, client: AsyncClient, analyst_user):
        token = await get_auth_token(client, "analyst@example.com", "TestAnalyst@123!")
        resp = await client.post(
            "/api/v1/events/ingest",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "source_system": "test",
                "event_type": "NETWORK",
                "severity": "LOW",
                "description": "Test",
                "source_ip": "not-an-ip",
            }
        )
        assert resp.status_code == 422

    async def test_duplicate_event_rejected(self, client: AsyncClient, analyst_user):
        token = await get_auth_token(client, "analyst@example.com", "TestAnalyst@123!")
        payload = {
            "source_system": "dedup-test",
            "event_type": "AUTHENTICATION",
            "severity": "LOW",
            "source_ip": "192.0.2.5",
            "username": "dupuser",
            "hostname": "dup-host",
            "description": "Duplicate test event",
            "timestamp": "2024-01-01T12:00:00Z",
            "is_synthetic": True,
        }
        r1 = await client.post(
            "/api/v1/events/ingest",
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
        )
        assert r1.status_code == 201
        r2 = await client.post(
            "/api/v1/events/ingest",
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
        )
        assert r2.status_code == 409


class TestEventListing:
    async def test_list_events_empty(self, client: AsyncClient, admin_user):
        token = await get_auth_token(client, "admin@example.com", "TestAdmin@123!")
        resp = await client.get(
            "/api/v1/events",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data

    async def test_list_events_with_severity_filter(self, client: AsyncClient, analyst_user):
        token = await get_auth_token(client, "analyst@example.com", "TestAnalyst@123!")
        resp = await client.get(
            "/api/v1/events?severity=CRITICAL",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200

    async def test_get_event_not_found(self, client: AsyncClient, admin_user):
        import uuid
        token = await get_auth_token(client, "admin@example.com", "TestAdmin@123!")
        resp = await client.get(
            f"/api/v1/events/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 404

    async def test_pagination_params(self, client: AsyncClient, admin_user):
        token = await get_auth_token(client, "admin@example.com", "TestAdmin@123!")
        resp = await client.get(
            "/api/v1/events?page=1&page_size=5",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] == 5
