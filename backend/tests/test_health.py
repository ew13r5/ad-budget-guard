"""Tests for health check and main app."""
import os
import pytest


@pytest.fixture(autouse=True)
def _set_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost/test")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    monkeypatch.setenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
    monkeypatch.setenv("META_APP_ID", "123")
    monkeypatch.setenv("META_APP_SECRET", "secret")
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("ENCRYPTION_KEY", "dGVzdGtleQ==")
    from app.config import get_settings
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_health_returns_200():
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_stub_routes_return_501_or_auth():
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        # Rules and monitoring now require auth (implemented in split 09)
        response = await client.get("/api/rules")
        assert response.status_code in (401, 422)

        response = await client.get("/api/monitoring/spend")
        assert response.status_code in (401, 422)

        response = await client.get("/api/alerts")
        assert response.status_code in (401, 501)

        response = await client.post("/api/simulation/start")
        assert response.status_code in (401, 501)


@pytest.mark.asyncio
async def test_protected_route_requires_auth():
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/accounts")
        assert response.status_code == 401
