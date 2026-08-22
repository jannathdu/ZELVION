from functools import lru_cache
from typing import Literal, Self
from urllib.parse import urlparse

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ZELVION API"
    app_version: str = "0.1.0"

    environment: Literal[
        "development",
        "test",
        "production",
    ] = "development"

    frontend_origin: str = "http://localhost:5173"

    db_host: str
    db_port: int = 5432
    db_name: str
    db_user: str
    db_password: SecretStr

    jwt_secret_key: SecretStr
    jwt_algorithm: Literal["HS256"] = "HS256"

    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    enable_mock_subscription_activation: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_environment_security(self) -> Self:
        if self.environment != "production":
            return self

        if self.enable_mock_subscription_activation:
            raise ValueError(
                "Mock subscription activation must be disabled "
                "in production."
            )

        jwt_secret = (
            self.jwt_secret_key.get_secret_value()
        )

        if len(jwt_secret) < 32:
            raise ValueError(
                "Production JWT secret must contain "
                "at least 32 characters."
            )

        origin = urlparse(
            self.frontend_origin,
        )

        hostname = (
            origin.hostname or ""
        ).lower()

        if hostname in {
            "localhost",
            "127.0.0.1",
            "::1",
        }:
            raise ValueError(
                "Production frontend origin cannot "
                "use localhost."
            )

        if origin.scheme != "https":
            raise ValueError(
                "Production frontend origin must "
                "use HTTPS."
            )

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()