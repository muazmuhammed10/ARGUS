"""ARGUS — Incident management tests."""

import pytest
from httpx import AsyncClient
from tests.conftest import get_auth_token

pytestmark = pytest.mark.asyncio


class TestIncidentLifecycle:
    async def test_create_incident(self, client: AsyncClient, analyst_user):
        token = await get_auth_token(client, "analyst@example.com", "TestAnalyst@123!")
        resp = await client.post(
            "/api/v1/incidents",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "Test Security Incident",
                "description": "Suspicious activity detected on web server",
                "severity": "HIGH",
            }
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["title"] == "Test Security Incident"
        assert data["status"] == "NEW"
        assert data["severity"] == "HIGH"

    async def test_viewer_cannot_create_incident(self, client: AsyncClient, viewer_user):
        token = await get_auth_token(client, "viewer@example.com", "TestViewer@123!")
        resp = await client.post(
            "/api/v1/incidents",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "x", "description": "x", "severity": "LOW"}
        )
        assert resp.status_code == 403

    async def test_list_incidents(self, client: AsyncClient, admin_user):
        token = await get_auth_token(client, "admin@example.com", "TestAdmin@123!")
        resp = await client.get("/api/v1/incidents", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data

    async def test_update_incident_status(self, client: AsyncClient, analyst_user):
        token = await get_auth_token(client, "analyst@example.com", "TestAnalyst@123!")
        # Create first
        create_resp = await client.post(
            "/api/v1/incidents",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "Incident to update", "description": "Test", "severity": "MEDIUM"},
        )
        assert create_resp.status_code == 201
        incident_id = create_resp.json()["id"]

        # Update status
        update_resp = await client.patch(
            f"/api/v1/incidents/{incident_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": "TRIAGED"},
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["status"] == "TRIAGED"

    async def test_get_incident_not_found(self, client: AsyncClient, admin_user):
        import uuid
        token = await get_auth_token(client, "admin@example.com", "TestAdmin@123!")
        resp = await client.get(
            f"/api/v1/incidents/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 404

    async def test_incident_requires_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/incidents")
        assert resp.status_code == 401

    async def test_incident_lifecycle_new_to_resolved(self, client: AsyncClient, analyst_user):
        token = await get_auth_token(client, "analyst@example.com", "TestAnalyst@123!")
        # Create
        r = await client.post(
            "/api/v1/incidents",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "Full lifecycle test", "description": "Testing full lifecycle", "severity": "LOW"},
        )
        assert r.status_code == 201
        inc_id = r.json()["id"]

        # Triage
        r = await client.patch(f"/api/v1/incidents/{inc_id}", headers={"Authorization": f"Bearer {token}"}, json={"status": "TRIAGED"})
        assert r.json()["status"] == "TRIAGED"

        # Investigate
        r = await client.patch(f"/api/v1/incidents/{inc_id}", headers={"Authorization": f"Bearer {token}"}, json={"status": "INVESTIGATING"})
        assert r.json()["status"] == "INVESTIGATING"

        # Resolve
        r = await client.patch(f"/api/v1/incidents/{inc_id}", headers={"Authorization": f"Bearer {token}"}, json={"status": "RESOLVED", "resolution_summary": "Resolved after investigation"})
        assert r.json()["status"] == "RESOLVED"
        assert r.json()["resolution_summary"] == "Resolved after investigation"
        assert r.json()["resolved_at"] is not None
