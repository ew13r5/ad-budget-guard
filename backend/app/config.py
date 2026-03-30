from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    database_url: str
    # Redis
    redis_url: str
    # Celery
    celery_broker_url: str
    celery_result_backend: str
    # Meta API
    meta_app_id: str
    meta_app_secret: str
    meta_api_version: str = "v19.0"
    facebook_redirect_uri: str = "http://localhost:3020/auth/callback"
    # Auth
    secret_key: str
    encryption_key: str
    # Default mode for new accounts
    ad_data_mode: Literal["simulation", "meta_sandbox", "production"] = "simulation"
    # Monitoring
    consecutive_threshold: int = 2
    forecast_lookback_hours: int = 4
    anomaly_lookback_days: int = 7
    monitoring_lock_ttl: int = 280
    # Alerts
    alert_cooldown_seconds: int = 300
    telegram_bot_token: str = ""
    # SMTP Email
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_use_ssl: bool = False
    # Reports
    report_logo_path: str = ""
    report_agency_name: str = "Ad Budget Guard"
    report_storage_dir: str = "/app/reports"
    # Google Sheets
    google_service_account_json: str = ""
    # Sentry
    sentry_dsn: str = ""
    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
