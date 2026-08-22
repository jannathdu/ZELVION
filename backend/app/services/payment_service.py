import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.payment_transaction import PaymentTransaction
from backend.app.models.subscription_plan import SubscriptionPlan
from backend.app.models.user_subscription import UserSubscription


class PaymentServiceError(Exception):
    """Base payment service error."""


class PlanNotFoundError(PaymentServiceError):
    """Raised when subscription plan does not exist."""


class PaymentNotFoundError(PaymentServiceError):
    """Raised when a payment does not exist for the user."""


class InvalidPaymentStatusError(PaymentServiceError):
    """Raised for invalid payment transitions."""


class ActiveSubscriptionPaymentError(PaymentServiceError):
    """Raised when a user already has a valid active subscription."""


def get_payment_for_update(
    database: Session,
    *,
    user_id: uuid.UUID,
    payment_id: uuid.UUID,
) -> PaymentTransaction:
    """
    Return and lock a payment belonging to the user.

    The row lock allows payment-success processing to inspect
    and update a payment without a concurrent callback changing
    the same row in between.
    """

    payment = database.scalar(
        select(PaymentTransaction)
        .where(
            PaymentTransaction.id == payment_id,
            PaymentTransaction.user_id == user_id,
        )
        .with_for_update()
    )

    if payment is None:
        raise PaymentNotFoundError

    return payment


def create_payment_order(
    database: Session,
    *,
    user_id: uuid.UUID,
    subscription_plan_id: uuid.UUID,
    provider: str,
) -> PaymentTransaction:
    """Create a pending payment transaction."""

    now = datetime.now(timezone.utc)

    active_subscription = database.scalar(
        select(UserSubscription).where(
            UserSubscription.user_id == user_id,
            UserSubscription.status == "active",
            UserSubscription.ends_at > now,
        )
    )

    if active_subscription is not None:
        raise ActiveSubscriptionPaymentError

    plan = database.scalar(
        select(SubscriptionPlan).where(
            SubscriptionPlan.id == subscription_plan_id,
            SubscriptionPlan.is_active.is_(True),
        )
    )

    if plan is None:
        raise PlanNotFoundError

    payment = PaymentTransaction(
        user_id=user_id,
        subscription_plan_id=subscription_plan_id,
        amount=plan.price_minor_units,
        currency=plan.currency,
        provider=provider,
        status="pending",
    )

    database.add(payment)
    database.commit()
    database.refresh(payment)

    return payment


def mark_payment_success(
    database: Session,
    *,
    user_id: uuid.UUID,
    payment_id: uuid.UUID,
    provider_transaction_id: str,
    commit: bool = True,
) -> PaymentTransaction:
    """
    Mark the current user's pending payment as successful.

    When commit=False, changes are flushed but not committed.
    This allows payment success and subscription activation
    to be committed as one atomic database transaction.
    """

    payment = get_payment_for_update(
        database,
        user_id=user_id,
        payment_id=payment_id,
    )

    if payment.status != "pending":
        raise InvalidPaymentStatusError

    payment.status = "success"
    payment.provider_transaction_id = (
        provider_transaction_id
    )
    payment.paid_at = datetime.now(timezone.utc)

    database.flush()

    if commit:
        database.commit()
        database.refresh(payment)

    return payment


def get_payment_history(
    database: Session,
    *,
    user_id: uuid.UUID,
) -> list[PaymentTransaction]:
    """Return payment history for a user."""

    payments = database.scalars(
        select(PaymentTransaction)
        .where(
            PaymentTransaction.user_id == user_id,
        )
        .order_by(
            PaymentTransaction.created_at.desc(),
        )
    ).all()

    return list(payments)