import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.data_usage import DataUsage
from backend.app.models.user_subscription import UserSubscription


class DataUsageServiceError(Exception):
    """Base exception for data usage rules."""


class NoActiveSubscriptionError(DataUsageServiceError):
    """Raised when no active subscription exists."""


class DataQuotaExceededError(DataUsageServiceError):
    """Raised when quota is exceeded."""


def record_usage(
    database: Session,
    *,
    user_id: uuid.UUID,
    bytes_used: int,
    record_type: str = "total",
    recorded_at: datetime | None = None,
) -> DataUsage:
    """Record traffic usage for an active subscription."""

    now = recorded_at or datetime.now(timezone.utc)

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

    if subscription.data_limit_bytes is not None:
        used_bytes = database.scalar(
            select(func.coalesce(func.sum(DataUsage.bytes_used), 0))
            .where(
                DataUsage.subscription_id == subscription.id,
            )
        )

        if used_bytes + bytes_used > subscription.data_limit_bytes:
            raise DataQuotaExceededError

    usage = DataUsage(
        user_id=user_id,
        subscription_id=subscription.id,
        bytes_used=bytes_used,
        record_type=record_type,
        created_at=now,
    )

    database.add(usage)
    database.commit()
    database.refresh(usage)

    return usage

def get_usage_summary(
    database: Session,
    *,
    user_id: uuid.UUID,
) -> dict[str, int | None]:
    """Return current subscription usage summary."""

    now = datetime.now(timezone.utc)

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

    used_bytes = database.scalar(
        select(func.coalesce(func.sum(DataUsage.bytes_used), 0))
        .where(
            DataUsage.subscription_id == subscription.id,
        )
    )

    remaining_bytes = None

    if subscription.data_limit_bytes is not None:
        remaining_bytes = max(
            subscription.data_limit_bytes - used_bytes,
            0,
        )

    return {
        "used_bytes": used_bytes,
        "limit_bytes": subscription.data_limit_bytes,
        "remaining_bytes": remaining_bytes,
    }