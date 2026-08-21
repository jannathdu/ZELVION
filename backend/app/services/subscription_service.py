import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models.subscription_plan import SubscriptionPlan
from backend.app.models.user_subscription import UserSubscription


class SubscriptionServiceError(Exception):
    """Base exception for subscription business rules."""


class SubscriptionPlanUnavailableError(SubscriptionServiceError):
    """Raised when a requested plan cannot be activated."""


class ActiveSubscriptionExistsError(SubscriptionServiceError):
    """Raised when a user already has a valid active subscription."""
class NoActiveSubscriptionError(SubscriptionServiceError):
    """Raised when a user has no valid active subscription to renew."""

def activate_subscription(
    database: Session,
    *,
    user_id: uuid.UUID,
    plan_id: uuid.UUID,
    activated_at: datetime | None = None,
) -> UserSubscription:
    """Activate an available plan for a user."""

    now = activated_at or datetime.now(timezone.utc)

    plan = database.scalar(
        select(SubscriptionPlan).where(
            SubscriptionPlan.id == plan_id,
            SubscriptionPlan.is_active.is_(True),
        )
    )

    if plan is None:
        raise SubscriptionPlanUnavailableError

    database.execute(
        update(UserSubscription)
        .where(
            UserSubscription.user_id == user_id,
            UserSubscription.status == "active",
            UserSubscription.ends_at <= now,
        )
        .values(
            status="expired",
            updated_at=now,
        )
    )

    active_subscription = database.scalar(
        select(UserSubscription)
        .where(
            UserSubscription.user_id == user_id,
            UserSubscription.status == "active",
            UserSubscription.ends_at > now,
        )
        .with_for_update()
    )

    if active_subscription is not None:
        database.rollback()
        raise ActiveSubscriptionExistsError

    subscription = UserSubscription(
        user_id=user_id,
        plan_id=plan.id,
        status="active",
        price_minor_units=plan.price_minor_units,
        currency=plan.currency,
        duration_days=plan.duration_days,
        data_limit_bytes=plan.data_limit_bytes,
        max_devices=plan.max_devices,
        starts_at=now,
        ends_at=now + timedelta(days=plan.duration_days),
    )

    database.add(subscription)

    try:
        database.commit()
    except IntegrityError:
        database.rollback()
        raise ActiveSubscriptionExistsError from None

    database.refresh(subscription)

    return subscription

def renew_subscription(
    database: Session,
    *,
    user_id: uuid.UUID,
    renewed_at: datetime | None = None,
) -> UserSubscription:
    """Extend a user's valid active subscription."""

    now = renewed_at or datetime.now(timezone.utc)

    database.execute(
        update(UserSubscription)
        .where(
            UserSubscription.user_id == user_id,
            UserSubscription.status == "active",
            UserSubscription.ends_at <= now,
        )
        .values(
            status="expired",
            updated_at=now,
        )
    )

    subscription = database.scalar(
        select(UserSubscription)
        .where(
            UserSubscription.user_id == user_id,
            UserSubscription.status == "active",
            UserSubscription.ends_at > now,
        )
        .with_for_update()
    )
    if subscription is None:
        database.commit()
        raise NoActiveSubscriptionError

    subscription.ends_at = (
        subscription.ends_at
        + timedelta(days=subscription.duration_days)
    )
    subscription.updated_at = now

    database.commit()
    database.refresh(subscription)

    return subscription