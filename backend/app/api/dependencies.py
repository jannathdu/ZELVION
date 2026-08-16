import uuid
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from sqlalchemy.orm import Session

from backend.app.core.security import decode_token
from backend.app.db.session import get_db
from backend.app.models.user import User


bearer_scheme = HTTPBearer(auto_error=False)
DatabaseSession = Annotated[Session, Depends(get_db)]


def authentication_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired access token",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    database: DatabaseSession,
) -> User:
    if credentials is None:
        raise authentication_error()

    try:
        payload = decode_token(credentials.credentials)

        if payload["type"] != "access":
            raise jwt.InvalidTokenError

        user_id = uuid.UUID(payload["sub"])
    except (jwt.InvalidTokenError, ValueError, KeyError):
        raise authentication_error() from None

    user = database.get(User, user_id)

    if user is None or not user.is_active:
        raise authentication_error()

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]