import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models.device import Device
from backend.app.models.user_subscription import UserSubscription


class DeviceServiceError(Exception):
    """Base exception for device business rules."""


class NoActiveSubscriptionError(DeviceServiceError):
    """Raised when a user has no active subscription."""


class DeviceLimitReachedError(DeviceServiceError):
    """Raised when maximum device limit is reached."""


class DuplicateDeviceError(DeviceServiceError):
    """Raised when device already exists."""


def register_device(
    database: Session,
    *,
    user_id: uuid.UUID,
    device_key_hash: str,
    name: str,
    platform: str,
    registered_at: datetime | None = None,
) -> Device:
    """Register a new device for a subscribed user."""

    now = registered_at or datetime.now(timezone.utc)

    subscription = database.scalar(
        select(UserSubscription)
        .where(
            UserSubscription.user_id == user_id,
            UserSubscription.status == "active",
            UserSubscription.ends_at > now,
        )
        .order_by(UserSubscription.ends_at.desc())
    )

    if subscription is None:
        raise NoActiveSubscriptionError

    active_device_count = database.scalar(
        select(func.count(Device.id))
        .where(
            Device.user_id == user_id,
            Device.is_active.is_(True),
        )
    )

    if active_device_count >= subscription.max_devices:
        raise DeviceLimitReachedError

    existing_device = database.scalar(
        select(Device).where(
            Device.device_key_hash == device_key_hash
        )
    )

    if existing_device is not None:
        raise DuplicateDeviceError

    device = Device(
        user_id=user_id,
        device_key_hash=device_key_hash,
        name=name,
        platform=platform,
        is_active=True,
        last_seen_at=now,
    )

    database.add(device)

    try:
        database.commit()
    except IntegrityError:
        database.rollback()
        raise DuplicateDeviceError from None

    database.refresh(device)

    return device

def revoke_device(
    database: Session,
    *,
    user_id: uuid.UUID,
    device_id: uuid.UUID,
    revoked_at: datetime | None = None,
) -> Device:
    """Deactivate a user's device."""

    now = revoked_at or datetime.now(timezone.utc)

    device = database.scalar(
        select(Device)
        .where(
            Device.id == device_id,
            Device.user_id == user_id,
            Device.is_active.is_(True),
        )
        .with_for_update()
    )

    if device is None:
        raise DeviceServiceError

    device.is_active = False
    device.revoked_at = now

    database.commit()
    database.refresh(device)

    return device

def list_user_devices(
    database: Session,
    *,
    user_id: uuid.UUID,
) -> list[Device]:
    """Return all devices belonging to a user."""

    statement = (
        select(Device)
        .where(
            Device.user_id == user_id,
        )
        .order_by(
            Device.created_at.desc(),
        )
    )

    return list(database.scalars(statement).all())