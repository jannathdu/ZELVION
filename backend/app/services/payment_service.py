import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.payment_transaction import (
    PaymentTransaction,
)
from backend.app.models.subscription_plan import (
    SubscriptionPlan,
)


class PaymentServiceError(Exception):
    """Base payment service error."""


class PlanNotFoundError(PaymentServiceError):
    """Raised when subscription plan does not exist."""


class InvalidPaymentStatusError(PaymentServiceError):
    """Raised for invalid payment transitions."""


def create_payment_order(
    database: Session,
    *,
    user_id: uuid.UUID,
    subscription_plan_id: uuid.UUID,
    provider: str,
) -> PaymentTransaction:
    """Create a pending payment transaction."""

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
    payment_id: uuid.UUID,
    provider_transaction_id: str,
) -> PaymentTransaction:
    """Mark a payment transaction as successful."""

    payment = database.scalar(
        select(PaymentTransaction).where(
            PaymentTransaction.id == payment_id,
        )
    )

    if payment is None:
        raise PaymentServiceError

    if payment.status != "pending":
        raise InvalidPaymentStatusError

    payment.status = "success"
    payment.provider_transaction_id = (
        provider_transaction_id
    )
    payment.paid_at = datetime.now(timezone.utc)

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