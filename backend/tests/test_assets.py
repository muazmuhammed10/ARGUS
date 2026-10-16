"""ARGUS — Asset inventory tests."""

import pytest
from httpx import AsyncClient
from tests.conftest import get_auth_token

pytestmark = pytest.mark.asyncio


class TestAssets:
    async def test_create_asset(self, client: AsyncClient, analyst_user):
        token = await get_auth_token(client, "analyst@example.com", "TestAnalyst@123!")
        resp = await client.post(
            "/api/v1/assets",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Test Web Server",
                "hostname": "web-01.example.com",
                "ip_address": "192.0.2.10",
                "operating_system": "Ubuntu 22.04",
                "environment": "PRODUCTION",
                "criticality": "HIGH",
                "owner": "Platform Team",
            }
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["name"] == "Test Web Server"
        assert data["environment"] == "PRODUCTION"
        assert data["criticality"] == "HIGH"

    async def test_viewer_cannot_create_asset(self, client: AsyncClient, viewer_user):
        token = await get_auth_token(client, "viewer@example.com", "TestViewer@123!")
        resp = await client.post(
            "/api/v1/assets",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Test", "environment": "UNKNOWN", "criticality": "LOW"},
        )
        assert resp.status_code == 403

    async def test_list_assets(self, client: AsyncClient, admin_user):
        token = await get_auth_token(client, "admin@example.com", "TestAdmin@123!")
        resp = await client.get("/api/v1/assets", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert "items" in resp.json()

    async def test_get_asset_not_found(self, client: AsyncClient, admin_user):
        import uuid
        token = await get_auth_token(client, "admin@example.com", "TestAdmin@123!")
        resp = await client.get(f"/api/v1/assets/{uuid.uuid4()}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 404

    async def test_update_asset(self, client: AsyncClient, analyst_user):
        token = await get_auth_token(client, "analyst@example.com", "TestAnalyst@123!")
        r = await client.post(
            "/api/v1/assets",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Asset to update", "environment": "STAGING", "criticality": "LOW"},
        )
        assert r.status_code == 201
        asset_id = r.json()["id"]

        update_r = await client.patch(
            f"/api/v1/assets/{asset_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"criticality": "CRITICAL", "owner": "Security Team"},
        )
        assert update_r.status_code == 200
        assert update_r.json()["criticality"] == "CRITICAL"
        assert update_r.json()["owner"] == "Security Team"

    async def test_assets_require_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/assets")
        assert resp.status_code == 401
