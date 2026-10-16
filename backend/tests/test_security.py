"""
ARGUS — Security utility unit tests.
Tests password hashing and JWT token functions.
"""

import pytest
from datetime import datetime, timezone, timedelta
from jose import JWTError
import uuid

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)


class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        pw = "MySecret@Pass123!"
        h = hash_password(pw)
        assert h != pw
        assert "argon2" in h.lower()

    def test_correct_password_verifies(self):
        pw = "Correct@Horse123!"
        h = hash_password(pw)
        assert verify_password(pw, h) is True

    def test_wrong_password_fails(self):
        h = hash_password("Correct@Horse123!")
        assert verify_password("WrongPassword@123!", h) is False

    def test_different_hashes_for_same_password(self):
        pw = "SamePass@123!"
        h1 = hash_password(pw)
        h2 = hash_password(pw)
        assert h1 != h2  # Argon2 uses random salt


class TestAccessToken:
    def test_create_and_decode(self):
        uid = str(uuid.uuid4())
        token = create_access_token(subject=uid, role="ADMIN")
        payload = decode_token(token)
        assert payload["sub"] == uid
        assert payload["role"] == "ADMIN"
        assert payload["type"] == "access"

    def test_expired_token_raises(self):
        import os
        # Temporarily override expiry via a manual expired token
        from jose import jwt
        from app.core.config import settings
        payload = {
            "sub": str(uuid.uuid4()),
            "role": "VIEWER",
            "type": "access",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        with pytest.raises(JWTError):
            decode_token(token)

    def test_tampered_token_raises(self):
        uid = str(uuid.uuid4())
        token = create_access_token(subject=uid, role="VIEWER")
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(JWTError):
            decode_token(tampered)


class TestRefreshToken:
    def test_refresh_token_type(self):
        uid = str(uuid.uuid4())
        token = create_refresh_token(subject=uid)
        payload = decode_token(token)
        assert payload["type"] == "refresh"
        assert payload["sub"] == uid

    def test_access_token_cannot_be_used_as_refresh(self):
        uid = str(uuid.uuid4())
        access = create_access_token(subject=uid, role="ADMIN")
        payload = decode_token(access)
        assert payload["type"] != "refresh"
