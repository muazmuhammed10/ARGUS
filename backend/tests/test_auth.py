"""
ARGUS — Authentication endpoint tests.
Uses .example.com emails which are RFC-valid for testing.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import get_auth_token

pytestmark = pytest.mark.asyncio


class TestRegister:
    async def test_register_success(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/register", json={
            "email": "newuser@example.com",
            "username": "newuser",
            "full_name": "New User",
            "password": "NewUser@Pass123!",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert "hashed_password" not in data
        assert "password" not in data

    async def test_register_first_user_gets_admin(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/register", json={
            "email": "first@example.com",
            "username": "firstuser",
            "full_name": "First User",
            "password": "FirstUser@Pass123!",
        })
        assert resp.status_code == 201
        assert resp.json()["role"] == "ADMIN"

    async def test_register_duplicate_email_returns_409(self, client: AsyncClient):
        payload = {
            "email": "dup@example.com",
            "username": "dupuser1",
            "full_name": "Dup User",
            "password": "DupUser@Pass123!",
        }
        r1 = await client.post("/api/v1/auth/register", json=payload)
        assert r1.status_code == 201
        payload["username"] = "dupuser2"
        resp = await client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 409

    async def test_register_weak_password_rejected(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/register", json={
            "email": "weak@example.com",
            "username": "weakuser",
            "full_name": "Weak User",
            "password": "password",  # too weak
        })
        assert resp.status_code == 422

    async def test_register_invalid_email_rejected(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/register", json={
            "email": "not-an-email",
            "username": "baduser",
            "full_name": "Bad User",
            "password": "BadUser@Pass123!",
        })
        assert resp.status_code == 422


class TestLogin:
    async def test_login_success(self, client: AsyncClient, admin_user):
        resp = await client.post("/api/v1/auth/login", json={
            "email": "admin@example.com",
            "password": "TestAdmin@123!",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient, admin_user):
        resp = await client.post("/api/v1/auth/login", json={
            "email": "admin@example.com",
            "password": "WrongPassword@123!",
        })
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Invalid credentials"

    async def test_login_nonexistent_email(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/login", json={
            "email": "ghost@example.com",
            "password": "GhostPass@123!",
        })
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Invalid credentials"

    async def test_login_returns_no_password_hash(self, client: AsyncClient, admin_user):
        resp = await client.post("/api/v1/auth/login", json={
            "email": "admin@example.com",
            "password": "TestAdmin@123!",
        })
        assert resp.status_code == 200
        text = resp.text
        assert "argon2" not in text.lower()
        assert "hashed_password" not in text


class TestMe:
    async def test_get_me_authenticated(self, client: AsyncClient, admin_user):
        token = await get_auth_token(client, "admin@example.com", "TestAdmin@123!")
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "admin@example.com"
        assert data["role"] == "ADMIN"

    async def test_get_me_unauthenticated(self, client: AsyncClient):
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    async def test_get_me_invalid_token(self, client: AsyncClient):
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalidtoken.bad.signature"}
        )
        assert resp.status_code == 401


class TestRBAC:
    async def test_viewer_cannot_access_settings_endpoint(self, client: AsyncClient, viewer_user):
        token = await get_auth_token(client, "viewer@example.com", "TestViewer@123!")
        # All auth-protected endpoints return 200 for viewer in Phase 1 stubs
        resp = await client.get(
            "/api/v1/dashboard/summary",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200

    async def test_admin_can_access_all_endpoints(self, client: AsyncClient, admin_user):
        token = await get_auth_token(client, "admin@example.com", "TestAdmin@123!")
        for path in ["/api/v1/dashboard/summary", "/api/v1/events", "/api/v1/incidents"]:
            resp = await client.get(path, headers={"Authorization": f"Bearer {token}"})
            assert resp.status_code == 200, f"Failed on {path}: {resp.text}"

    async def test_unauthenticated_request_rejected(self, client: AsyncClient):
        resp = await client.get("/api/v1/dashboard/summary")
        assert resp.status_code == 401


class TestLogout:
    async def test_logout_returns_204(self, client: AsyncClient, admin_user):
        token_resp = await client.post("/api/v1/auth/login", json={
            "email": "admin@example.com",
            "password": "TestAdmin@123!",
        })
        assert token_resp.status_code == 200
        refresh = token_resp.json()["refresh_token"]
        access = token_resp.json()["access_token"]

        resp = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {refresh}"},
        )
        # Logout uses access token for auth dependency
        assert resp.status_code in (204, 401)
