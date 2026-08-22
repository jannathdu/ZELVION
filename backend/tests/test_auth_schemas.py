import pytest
from pydantic import ValidationError

from backend.app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
)


def test_valid_registration_data() -> None:
    registration = RegisterRequest(
        email="user@example.com",
        password="Strong-Password-123!",
    )

    assert str(registration.email) == "user@example.com"


@pytest.mark.parametrize(
    "password",
    [
        "short",
        "alllowercase123!",
        "ALLUPPERCASE123!",
        "NoNumberPassword!",
        "NoSpecialPassword123",
    ],
)
def test_weak_registration_password_is_rejected(
    password: str,
) -> None:
    with pytest.raises(ValidationError):
        RegisterRequest(
            email="user@example.com",
            password=password,
        )


def test_invalid_email_is_rejected() -> None:
    with pytest.raises(ValidationError):
        RegisterRequest(
            email="not-an-email",
            password="Strong-Password-123!",
        )


def test_login_accepts_existing_password_format() -> None:
    login = LoginRequest(
        email="user@example.com",
        password="existing-password",
    )

    assert str(login.email) == "user@example.com"

def test_refresh_token_rejects_excessive_length() -> None:
    with pytest.raises(ValidationError):
        RefreshTokenRequest(
            refresh_token="x" * 4097,
        )


def test_refresh_token_accepts_normal_length() -> None:
    request = RefreshTokenRequest(
        refresh_token="test-refresh-token",
    )

    assert request.refresh_token == "test-refresh-token"