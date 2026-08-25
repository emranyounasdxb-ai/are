from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ARE_", case_sensitive=False)

    environment: Literal["local", "test", "production"] = "local"
    database_url: str = Field(repr=False)
    redis_url: str = Field(repr=False)
    cors_origins: str = "http://127.0.0.1:50001,http://127.0.0.1:50002"
    session_cookie_secure: bool = False
    session_lifetime_minutes: int = 480
    login_rate_limit_attempts: int = 5
    login_rate_limit_window_seconds: int = 900
    submission_rate_limit_attempts: int = 8
    submission_rate_limit_window_seconds: int = 900
    private_storage_backend: Literal["local", "object"] = "local"
    private_storage_path: str = "/app/private-storage"
    enquiry_retention_days: int | None = None
    application_retention_days: int | None = None
    overview_ai_provider: str | None = None
    overview_ai_model: str | None = None
    overview_ai_model_version: str | None = None
    overview_ai_api_key: SecretStr | None = None

    @model_validator(mode="after")
    def require_complete_overview_provider_configuration(self) -> Settings:
        values = (
            self.overview_ai_provider,
            self.overview_ai_model,
            self.overview_ai_model_version,
            self.overview_ai_api_key,
        )
        if any(values) and not all(values):
            raise ValueError(
                "ARE Overview AI configuration must provide provider, model, model version, "
                "and API key together"
            )
        return self

    @field_validator("database_url")
    @classmethod
    def require_postgresql(cls, value: str) -> str:
        if not value.startswith("postgresql+asyncpg://"):
            raise ValueError("ARE_DATABASE_URL must use postgresql+asyncpg")
        return value

    @field_validator("redis_url")
    @classmethod
    def require_redis(cls, value: str) -> str:
        if not value.startswith(("redis://", "rediss://")):
            raise ValueError("ARE_REDIS_URL must use redis:// or rediss://")
        return value

    @model_validator(mode="after")
    def require_secure_production_cookie(self) -> Settings:
        if self.environment == "production" and not self.session_cookie_secure:
            raise ValueError("Secure session cookies are mandatory in production")
        return self

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
