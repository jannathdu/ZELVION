import uuid
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)


router = APIRouter(prefix="/auth", tags=["authentication"])
settings = get_settings()

DatabaseSession = Annotated[Session, Depends(get_db)]

DUMMY_PASSWORD_HASH = hash_password(
    "Dummy-Password-Used-Only-For-Timing-123!"
)


def create_token_response(user_id: uuid.UUID) -> TokenResponse:
    subject = str(user_id)

    return TokenResponse(
        access_token=create_access_token(subject),
        refresh_token=create_refresh_token(subject),
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    payload: RegisterRequest,
    database: DatabaseSession,
) -> User:
    email = str(payload.email).strip().lower()

    existing_user = database.scalar(
        select(User).where(User.email == email)
    )
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(
        email=email,
        password_hash=hash_password(payload.password),
    )

    database.add(user)

    try:
        database.commit()
    except IntegrityError:
        database.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        ) from None

    database.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login_user(
    payload: LoginRequest,
    database: DatabaseSession,
) -> TokenResponse:
    email = str(payload.email).strip().lower()

    user = database.scalar(
        select(User).where(User.email == email)
    )

    password_hash_to_check = (
        user.password_hash
        if user is not None
        else DUMMY_PASSWORD_HASH
    )
    password_is_valid = verify_password(
        payload.password,
        password_hash_to_check,
    )

    if user is None or not password_is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    return create_token_response(user.id)


@router.post("/refresh", response_model=TokenResponse)
def refresh_tokens(
    payload: RefreshTokenRequest,
    database: DatabaseSession,
) -> TokenResponse:
    try:
        token_payload = decode_token(payload.refresh_token)

        if token_payload["type"] != "refresh":
            raise jwt.InvalidTokenError

        user_id = uuid.UUID(token_payload["sub"])
    except (jwt.InvalidTokenError, ValueError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    user = database.get(User, user_id)

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive account",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return create_token_response(user.id)