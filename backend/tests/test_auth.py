"""Tests for authentication: JWT, token service, RBAC."""
import os
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from jose import jwt


# Ensure settings can load
@pytest.fixture(autouse=True)
def _set_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost/test")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    monkeypatch.setenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
    monkeypatch.setenv("META_APP_ID", "123")
    monkeypatch.setenv("META_APP_SECRET", "secret")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-jwt")
    monkeypatch.setenv("ENCRYPTION_KEY", "dGVzdGtleQ==")
    # Clear lru_cache between tests
    from app.config import get_settings
    get_settings.cache_clear()


class TestJWTCreation:
    def test_create_access_token(self):
        from app.services.token_service import create_access_token
        uid = uuid4()
        token = create_access_token(uid)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_access_token_contains_user_id(self):
        from app.services.token_service import create_access_token, decode_token
        uid = uuid4()
        token = create_access_token(uid)
        payload = decode_token(token)
        assert payload["user_id"] == str(uid)
        assert payload["type"] == "access"

    def test_create_refresh_token(self):
        from app.services.token_service import create_refresh_token
        uid = uuid4()
        token = create_refresh_token(uid)
        assert isinstance(token, str)

    def test_refresh_token_type(self):
        from app.services.token_service import create_refresh_token, decode_token
        uid = uuid4()
        token = create_refresh_token(uid)
        payload = decode_token(token)
        assert payload["type"] == "refresh"


class TestTokenVerification:
    def test_verify_valid_access_token(self):
        from app.services.token_service import create_access_token, verify_access_token
        uid = uuid4()
        token = create_access_token(uid)
        result = verify_access_token(token)
        assert result == str(uid)

    def test_verify_expired_token_returns_none(self):
        from app.services.token_service import verify_access_token
        # Create manually expired token
        payload = {
            "user_id": str(uuid4()),
            "exp": datetime.utcnow() - timedelta(hours=1),
            "iat": datetime.utcnow() - timedelta(hours=2),
            "type": "access",
        }
        token = jwt.encode(payload, "test-secret-key-for-jwt", algorithm="HS256")
        result = verify_access_token(token)
        assert result is None

    def test_verify_malformed_token_returns_none(self):
        from app.services.token_service import verify_access_token
        result = verify_access_token("not.a.valid.token")
        assert result is None

    def test_verify_refresh_token_rejects_access_token(self):
        from app.services.token_service import create_access_token, verify_refresh_token
        uid = uuid4()
        token = create_access_token(uid)
        result = verify_refresh_token(token)
        assert result is None

    def test_verify_access_token_rejects_refresh_token(self):
        from app.services.token_service import create_refresh_token, verify_access_token
        uid = uuid4()
        token = create_refresh_token(uid)
        result = verify_access_token(token)
        assert result is None


class TestRoleHierarchy:
    def test_role_weights(self):
        from app.api.deps import _ROLE_WEIGHT
        from app.models.ad_account import UserRole
        assert _ROLE_WEIGHT[UserRole.owner] > _ROLE_WEIGHT[UserRole.manager]
        assert _ROLE_WEIGHT[UserRole.manager] > _ROLE_WEIGHT[UserRole.viewer]
