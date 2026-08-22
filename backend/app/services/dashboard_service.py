import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.data_usage import DataUsage
from backend.app.models.device import Device
from backend.app.models.payment_transaction import (
    PaymentTransaction,
)
from backend.app.models.subscription_plan import (
    SubscriptionPlan,
)
from backend.app.models.user import User
from backend.app.models.user_subscription import (
    UserSubscription,
)


def get_dashboard_data(
    database: Session,
    *,
    user_id: uuid.UUID,
) -> dict:
    now = datetime.now(timezone.utc)

    user = database.scalar(
        select(User).where(
            User.id == user_id,
        )
    )

    subscription = database.scalar(
        select(UserSubscription)
        .where(
            UserSubscription.user_id == user_id,
            UserSubscription.status == "active",
            UserSubscription.ends_at > now,
        )
        .order_by(
            UserSubscription.ends_at.desc(),
        )
    )

    plan_name = None

    if subscription is not None:
        plan = database.scalar(
            select(SubscriptionPlan).where(
                SubscriptionPlan.id
                == subscription.plan_id,
            )
        )

        if plan is not None:
            plan_name = plan.name

    used_bytes = 0

    if subscription is not None:
        used_bytes = (
            database.scalar(
                select(
                    func.coalesce(
                        func.sum(DataUsage.bytes_used),
                        0,
                    )
                ).where(
                    DataUsage.user_id == user_id,
                    DataUsage.subscription_id
                    == subscription.id,
                )
            )
            or 0
        )

    limit_bytes = None
    max_devices = None

    if subscription is not None:
        limit_bytes = subscription.data_limit_bytes
        max_devices = subscription.max_devices

    remaining_bytes = None

    if limit_bytes is not None:
        remaining_bytes = max(
            limit_bytes - used_bytes,
            0,
        )

    device_count = (
        database.scalar(
            select(func.count(Device.id)).where(
                Device.user_id == user_id,
                Device.is_active.is_(True),
            )
        )
        or 0
    )

    last_payment = None

    if subscription is not None:
        last_payment = database.scalar(
            select(PaymentTransaction)
            .where(
                PaymentTransaction.user_id == user_id,
                PaymentTransaction.subscription_plan_id
                == subscription.plan_id,
                PaymentTransaction.status == "success",
            )
            .order_by(
                PaymentTransaction.paid_at.desc(),
                PaymentTransaction.created_at.desc(),
            )
        )
    else:
        last_payment = database.scalar(
            select(PaymentTransaction)
            .where(
                PaymentTransaction.user_id == user_id,
            )
            .order_by(
                PaymentTransaction.created_at.desc(),
            )
        )

    return {
        "user": {
            "id": user.id,
            "email": user.email,
        },
        "subscription": {
            "plan_name": plan_name,
            "status": (
                subscription.status
                if subscription is not None
                else None
            ),
            "starts_at": (
                subscription.starts_at
                if subscription is not None
                else None
            ),
            "ends_at": (
                subscription.ends_at
                if subscription is not None
                else None
            ),
        },
        "usage": {
            "used_bytes": used_bytes,
            "limit_bytes": limit_bytes,
            "remaining_bytes": remaining_bytes,
        },
        "devices": {
            "total_devices": device_count,
            "max_devices": max_devices,
        },
        "payments": {
            "last_payment_status": (
                last_payment.status
                if last_payment is not None
                else None
            ),
            "last_payment_date": (
                last_payment.created_at
                if last_payment is not None
                else None
            ),
        },
    }