import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import CurrentUser
from backend.app.db.session import get_db
from backend.app.schemas.device import DeviceCreateRequest, DeviceResponse
from backend.app.services.device_service import (
    DeviceLimitReachedError,
    DuplicateDeviceError,
    NoActiveSubscriptionError,
    register_device,
)

router = APIRouter(
    prefix="/devices",
    tags=["devices"],
)

DatabaseSession = Annotated[Session, Depends(get_db)]

@router.post(
    "",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_device(
    payload: DeviceCreateRequest,
    current_user: CurrentUser,
    database: DatabaseSession,
) -> DeviceResponse:
    try:
        return register_device(
            database,
            user_id=current_user.id,
            device_key_hash=payload.device_key_hash,
            name=payload.name,
            platform=payload.platform,
        )

    except NoActiveSubscriptionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active subscription required",
        ) from None

    except DeviceLimitReachedError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Device limit reached",
        ) from None

    except DuplicateDeviceError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Device already exists",
        ) from None

@router.delete(
    "/{device_id}",
    response_model=DeviceResponse,
)
def delete_device(
    device_id: uuid.UUID,
    current_user: CurrentUser,
    database: DatabaseSession,
) -> DeviceResponse:
    from backend.app.services.device_service import (
        revoke_device,
    )

    try:
        return revoke_device(
            database,
            user_id=current_user.id,
            device_id=device_id,
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        ) from None

@router.get(
    "",
    response_model=list[DeviceResponse],
)
def get_my_devices(
    current_user: CurrentUser,
    database: DatabaseSession,
) -> list[DeviceResponse]:
    from backend.app.services.device_service import (
        list_user_devices,
    )

    return list_user_devices(
        database,
        user_id=current_user.id,
    )