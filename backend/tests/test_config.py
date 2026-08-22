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

def test_alipay_disabled_does_not_require_credentials() -> None:
    settings = Settings(
        **BASE_SETTINGS,
        environment="development",
        enable_alipay_payments=False,
        _env_file=None,
    )

    assert settings.enable_alipay_payments is False


def test_alipay_enabled_requires_configuration() -> None:
    with pytest.raises(ValidationError):
        Settings(
            **BASE_SETTINGS,
            environment="development",
            enable_alipay_payments=True,
            _env_file=None,
        )


def test_alipay_rejects_non_https_gateway() -> None:
    with pytest.raises(ValidationError):
        Settings(
            **BASE_SETTINGS,
            environment="development",
            enable_alipay_payments=True,
            alipay_app_id="test-app-id",
            alipay_app_private_key="test-private-key",
            alipay_public_key="test-public-key",
            alipay_gateway_url=(
                "http://openapi.alipay.com/gateway.do"
            ),
            alipay_notify_url=(
                "https://example.com/api/v1/payments/alipay/notify"
            ),
            _env_file=None,
        )


def test_alipay_rejects_non_https_notify_url() -> None:
    with pytest.raises(ValidationError):
        Settings(
            **BASE_SETTINGS,
            environment="development",
            enable_alipay_payments=True,
            alipay_app_id="test-app-id",
            alipay_app_private_key="test-private-key",
            alipay_public_key="test-public-key",
            alipay_gateway_url=(
                "https://openapi-sandbox.dl.alipaydev.com/gateway.do"
            ),
            alipay_notify_url=(
                "http://example.com/api/v1/payments/alipay/notify"
            ),
            _env_file=None,
        )


def test_production_rejects_nonproduction_alipay_gateway() -> None:
    with pytest.raises(ValidationError):
        Settings(
            **BASE_SETTINGS,
            environment="production",
            frontend_origin="https://app.zelvion.com",
            enable_mock_subscription_activation=False,
            enable_alipay_payments=True,
            alipay_app_id="production-app-id",
            alipay_app_private_key="production-private-key",
            alipay_public_key="production-public-key",
            alipay_gateway_url=(
                "https://openapi-sandbox.dl.alipaydev.com/gateway.do"
            ),
            alipay_notify_url=(
                "https://api.zelvion.com/api/v1/payments/alipay/notify"
            ),
            _env_file=None,
        )


def test_production_accepts_valid_alipay_config() -> None:
    settings = Settings(
        **BASE_SETTINGS,
        environment="production",
        frontend_origin="https://app.zelvion.com",
        enable_mock_subscription_activation=False,
        enable_alipay_payments=True,
        alipay_app_id="production-app-id",
        alipay_app_private_key="production-private-key",
        alipay_public_key="production-public-key",
        alipay_gateway_url=(
            "https://openapi.alipay.com/gateway.do"
        ),
        alipay_notify_url=(
            "https://api.zelvion.com/api/v1/payments/alipay/notify"
        ),
        _env_file=None,
    )

    assert settings.enable_alipay_payments is True
    assert (
        settings.alipay_gateway_url
        == "https://openapi.alipay.com/gateway.do"
    )