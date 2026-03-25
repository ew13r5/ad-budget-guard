"""Tests for Pydantic Settings configuration."""
import pytest
from pydantic import ValidationError


def _set_required_env(monkeypatch, **overrides):
    defaults = {
        "DATABASE_URL": "postgresql://test:test@localhost/test",
        "REDIS_URL": "redis://localhost:6379/0",
        "CELERY_BROKER_URL": "redis://localhost:6379/1",
        "CELERY_RESULT_BACKEND": "redis://localhost:6379/2",
        "META_APP_ID": "123",
        "META_APP_SECRET": "secret",
        "SECRET_KEY": "jwt-secret",
        "ENCRYPTION_KEY": "encryption-secret",
    }
    defaults.update(overrides)
    for k, v in defaults.items():
        monkeypatch.setenv(k, v)


class TestSettings:
    def test_settings_loads_from_env(self, monkeypatch):
        _set_required_env(monkeypatch)
        from app.config import Settings
        settings = Settings(_env_file=None)
        assert settings.database_url == "postgresql://test:test@localhost/test"

    def test_settings_validates_required_fields(self, monkeypatch):
        for key in [
            "DATABASE_URL", "REDIS_URL", "CELERY_BROKER_URL",
            "CELERY_RESULT_BACKEND", "META_APP_ID", "META_APP_SECRET",
            "SECRET_KEY", "ENCRYPTION_KEY",
        ]:
            monkeypatch.delenv(key, raising=False)
        from app.config import Settings
        with pytest.raises(ValidationError):
            Settings(_env_file=None)

    def test_default_ad_data_mode_is_simulation(self, monkeypatch):
        _set_required_env(monkeypatch)
        from app.config import Settings
        assert Settings(_env_file=None).ad_data_mode == "simulation"

    def test_meta_api_version_default(self, monkeypatch):
        _set_required_env(monkeypatch)
        from app.config import Settings
        assert Settings(_env_file=None).meta_api_version == "v19.0"

    def test_encryption_key_separate_from_secret_key(self, monkeypatch):
        _set_required_env(monkeypatch)
        from app.config import Settings
        settings = Settings(_env_file=None)
        assert settings.secret_key != settings.encryption_key
