from datetime import timedelta

import jwt
import pytest

from backend.app.core.security import (
    create_access_token,
    create_refresh_token,
    create_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hashing_and_verification() -> None:
    plain_password = "Strong-Test-Password-123!"
    hashed_password = hash_password(plain_password)

    assert hashed_password != plain_password
    assert verify_password(plain_password, hashed_password)
    assert not verify_password("Wrong-Password", hashed_password)


def test_access_token_creation_and_decoding() -> None:
    token = create_access_token("user-123")
    payload = decode_token(token)

    assert payload["sub"] == "user-123"
    assert payload["type"] == "access"
    assert payload["jti"]


def test_refresh_token_creation_and_decoding() -> None:
    token = create_refresh_token("user-123")
    payload = decode_token(token)

    assert payload["sub"] == "user-123"
    assert payload["type"] == "refresh"
    assert payload["jti"]


def test_expired_token_is_rejected() -> None:
    token = create_token(
        subject="user-123",
        token_type="access",
        expires_delta=timedelta(seconds=-1),
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(token)