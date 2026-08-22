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

    enable_alipay_payments: bool = False
    alipay_app_id: str | None = None
    alipay_app_private_key: SecretStr | None = None
    alipay_public_key: str | None = None
    alipay_gateway_url: str | None = None
    alipay_notify_url: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_environment_security(self) -> Self:
        if self.enable_alipay_payments:
            self._validate_alipay_config()

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

    def _validate_alipay_config(self) -> None:
        required_values = {
            "ALIPAY_APP_ID": self.alipay_app_id,
            "ALIPAY_APP_PRIVATE_KEY": (
                self.alipay_app_private_key
            ),
            "ALIPAY_PUBLIC_KEY": self.alipay_public_key,
            "ALIPAY_GATEWAY_URL": self.alipay_gateway_url,
            "ALIPAY_NOTIFY_URL": self.alipay_notify_url,
        }

        missing = [
            name
            for name, value in required_values.items()
            if value is None
            or (
                isinstance(value, str)
                and not value.strip()
            )
        ]

        if missing:
            raise ValueError(
                "Alipay payments are enabled but required "
                "configuration is missing: "
                + ", ".join(missing)
            )

        gateway = urlparse(
            self.alipay_gateway_url or "",
        )

        if gateway.scheme != "https":
            raise ValueError(
                "Alipay gateway URL must use HTTPS."
            )

        notify = urlparse(
            self.alipay_notify_url or "",
        )

        if notify.scheme != "https":
            raise ValueError(
                "Alipay notify URL must use HTTPS."
            )

        if self.environment == "production":
            if (
                gateway.hostname
                != "openapi.alipay.com"
            ):
                raise ValueError(
                    "Production Alipay gateway must use "
                    "openapi.alipay.com."
                )


@lru_cache
def get_settings() -> Settings:
    return Settings()