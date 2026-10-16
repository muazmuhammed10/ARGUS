"""ARGUS — Role-based access control tests."""

import pytest
from httpx import AsyncClient
from tests.conftest import get_auth_token

pytestmark = pytest.mark.asyncio


class TestRBACEnforcement:
    """Backend RBAC is the authoritative enforcement layer."""

    async def test_admin_can_list_users(self, client: AsyncClient, admin_user):
        token = await get_auth_token(client, "admin@example.com", "TestAdmin@123!")
        resp = await client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200

    async def test_analyst_cannot_list_users(self, client: AsyncClient, analyst_user):
        token = await get_auth_token(client, "analyst@example.com", "TestAnalyst@123!")
        resp = await client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 403

    async def test_viewer_cannot_list_users(self, client: AsyncClient, viewer_user):
        token = await get_auth_token(client, "viewer@example.com", "TestViewer@123!")
        resp = await client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 403

    async def test_viewer_can_read_events(self, client: AsyncClient, viewer_user):
        token = await get_auth_token(client, "viewer@example.com", "TestViewer@123!")
        resp = await client.get(
            "/api/v1/events",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200

    async def test_viewer_cannot_ingest_events(self, client: AsyncClient, viewer_user):
        token = await get_auth_token(client, "viewer@example.com", "TestViewer@123!")
        resp = await client.post(
            "/api/v1/events/ingest",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "source_system": "test",
                "event_type": "AUTHENTICATION",
                "severity": "LOW",
                "description": "Test",
            }
        )
        assert resp.status_code == 403

    async def test_viewer_cannot_create_investigation(self, client: AsyncClient, viewer_user):
        token = await get_auth_token(client, "viewer@example.com", "TestViewer@123!")
        resp = await client.post(
            "/api/v1/investigations",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "Unauthorized investigation"}
        )
        assert resp.status_code == 403

    async def test_analyst_can_update_rules(self, client: AsyncClient, analyst_user):
        """Analysts should NOT be able to update detection rules — admin only."""
        import uuid
        token = await get_auth_token(client, "analyst@example.com", "TestAnalyst@123!")
        resp = await client.patch(
            f"/api/v1/rules/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
            json={"is_enabled": False}
        )
        assert resp.status_code == 403

    async def test_admin_can_update_rules(self, client: AsyncClient, admin_user):
        """Admin can attempt to update rules (404 for non-existent rule is fine)."""
        import uuid
        token = await get_auth_token(client, "admin@example.com", "TestAdmin@123!")
        resp = await client.patch(
            f"/api/v1/rules/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
            json={"is_enabled": False}
        )
        # 404 is expected since rule doesn't exist, but not 403
        assert resp.status_code in (404, 200)

    async def test_disabled_user_cannot_authenticate(self, client: AsyncClient, db_session):
        """Disabled accounts cannot log in."""
        from app.core.security import hash_password
        from app.models.user import User, UserRole

        disabled = User(
            email="disabled@example.com",
            username="disableduser",
            full_name="Disabled User",
            hashed_password=hash_password("Disabled@Pass123!"),
            role=UserRole.VIEWER,
            is_active=False,
        )
        db_session.add(disabled)
        await db_session.commit()

        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "disabled@example.com", "password": "Disabled@Pass123!"}
        )
        assert resp.status_code in (401, 403)

    async def test_expired_token_rejected(self, client: AsyncClient, admin_user):
        """Expired tokens must be rejected."""
        from datetime import timedelta
        from jose import jwt
        from app.core.config import settings

        payload = {
            "sub": str(admin_user.id),
            "role": "ADMIN",
            "type": "access",
            "exp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc) - timedelta(seconds=1),
        }
        expired_token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert resp.status_code == 401

    async def test_refresh_token_rejected_as_access(self, client: AsyncClient, admin_user):
        """A refresh token cannot be used as an access token."""
        from app.core.security import create_refresh_token
        refresh = create_refresh_token(subject=admin_user.id)

        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {refresh}"}
        )
        assert resp.status_code == 401
