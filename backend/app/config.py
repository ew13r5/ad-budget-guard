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
    # Auth
    secret_key: str
    encryption_key: str
    # Default mode for new accounts
    ad_data_mode: Literal["simulation", "meta_sandbox", "production"] = "simulation"
    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
