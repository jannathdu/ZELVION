import pytest
from pydantic import ValidationError

from backend.app.core.config import Settings


BASE_SETTINGS = {
    "db_host": "localhost",
    "db_name": "zelvion_test",
    "db_user": "zelvion",
    "db_password": "test-db-password",
    "jwt_secret_key": (
        "this-is-a-strong-production-jwt-secret-key-123456"
    ),
}


def test_development_config_allows_localhost() -> None:
    settings = Settings(
        **BASE_SETTINGS,
        environment="development",
        frontend_origin="http://localhost:5173",
        enable_mock_subscription_activation=True,
        _env_file=None,
    )

    assert settings.environment == "development"
    assert settings.enable_mock_subscription_activation is True


def test_production_rejects_mock_activation() -> None:
    with pytest.raises(ValidationError):
        Settings(
            **BASE_SETTINGS,
            environment="production",
            frontend_origin="https://app.zelvion.com",
            enable_mock_subscription_activation=True,
            _env_file=None,
        )


def test_production_rejects_weak_jwt_secret() -> None:
    with pytest.raises(ValidationError):
        Settings(
            **{
                **BASE_SETTINGS,
                "jwt_secret_key": "short-secret",
            },
            environment="production",
            frontend_origin="https://app.zelvion.com",
            enable_mock_subscription_activation=False,
            _env_file=None,
        )


@pytest.mark.parametrize(
    "origin",
    [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://localhost",
    ],
)
def test_production_rejects_local_frontend_origin(
    origin: str,
) -> None:
    with pytest.raises(ValidationError):
        Settings(
            **BASE_SETTINGS,
            environment="production",
            frontend_origin=origin,
            enable_mock_subscription_activation=False,
            _env_file=None,
        )


def test_production_accepts_secure_config() -> None:
    settings = Settings(
        **BASE_SETTINGS,
        environment="production",
        frontend_origin="https://app.zelvion.com",
        enable_mock_subscription_activation=False,
        _env_file=None,
    )

    assert settings.environment == "production"
    assert settings.frontend_origin == "https://app.zelvion.com"
    assert settings.enable_mock_subscription_activation is False