import uuid

from sqlalchemy import delete, select

from backend.app.db.session import SessionLocal
from backend.app.models.subscription_plan import SubscriptionPlan
from backend.app.models.user import User
from backend.app.services.dashboard_service import (
    get_dashboard_data,
)
from backend.app.services.data_usage_service import (
    record_usage,
)
from backend.app.services.device_service import (
    register_device,
)
from backend.app.services.payment_service import (
    create_payment_order,
    mark_payment_success,
)
from backend.app.services.subscription_service import (
    activate_subscription,
)


def test_get_dashboard_data_returns_complete_summary() -> None:
    email = f"dashboard-service-{uuid.uuid4()}@example.com"

    try:
        with SessionLocal() as database:
            user = User(
                email=email,
                password_hash="test-only-password-hash",
            )

            database.add(user)
            database.commit()
            database.refresh(user)

            plan = database.scalar(
                select(SubscriptionPlan).where(
                    SubscriptionPlan.code == "monthly"
                )
            )

            assert plan is not None

            payment = create_payment_order(
                database,
                user_id=user.id,
                subscription_plan_id=plan.id,
                provider="alipay",
            )

            mark_payment_success(
                database,
                user_id=user.id,
                payment_id=payment.id,
                provider_transaction_id=(
                    f"DASHBOARD-{uuid.uuid4()}"
                ),
            )

            activate_subscription(
                database,
                user_id=user.id,
                plan_id=plan.id,
            )

            record_usage(
                database,
                user_id=user.id,
                bytes_used=8192,
            )

            register_device(
                database,
                user_id=user.id,
                device_key_hash="dashboard-test-device",
                name="Test Laptop",
                platform="windows",
            )

            dashboard = get_dashboard_data(
                database,
                user_id=user.id,
            )

            assert dashboard["user"]["email"] == email

            assert (
                dashboard["subscription"]["status"]
                == "active"
            )

            assert (
                dashboard["subscription"]["plan_name"]
                == plan.name
            )

            assert (
                dashboard["usage"]["used_bytes"]
                == 8192
            )

            assert (
                dashboard["devices"]["total_devices"]
                == 1
            )

            assert (
                dashboard["payments"]["last_payment_status"]
                == "success"
            )

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(
                    User.email == email
                )
            )
            database.commit()

def test_dashboard_ignores_elapsed_active_subscription() -> None:
    from datetime import datetime, timedelta, timezone

    from backend.app.models.user_subscription import (
        UserSubscription,
    )

    email = (
        f"dashboard-expired-{uuid.uuid4()}@example.com"
    )

    try:
        with SessionLocal() as database:
            user = User(
                email=email,
                password_hash="test-only-password-hash",
            )

            database.add(user)
            database.commit()
            database.refresh(user)

            plan = database.scalar(
                select(SubscriptionPlan).where(
                    SubscriptionPlan.code == "monthly"
                )
            )

            assert plan is not None

            now = datetime.now(timezone.utc)

            elapsed_subscription = UserSubscription(
                user_id=user.id,
                plan_id=plan.id,
                status="active",
                price_minor_units=plan.price_minor_units,
                currency=plan.currency,
                duration_days=plan.duration_days,
                data_limit_bytes=plan.data_limit_bytes,
                max_devices=plan.max_devices,
                starts_at=now - timedelta(days=2),
                ends_at=now - timedelta(days=1),
            )

            database.add(elapsed_subscription)
            database.commit()

            dashboard = get_dashboard_data(
                database,
                user_id=user.id,
            )

            assert (
                dashboard["subscription"]["plan_name"]
                is None
            )

            assert (
                dashboard["subscription"]["status"]
                is None
            )

            assert (
                dashboard["subscription"]["starts_at"]
                is None
            )

            assert (
                dashboard["subscription"]["ends_at"]
                is None
            )

            assert (
                dashboard["usage"]["used_bytes"]
                == 0
            )

            assert (
                dashboard["usage"]["limit_bytes"]
                is None
            )

            assert (
                dashboard["devices"]["max_devices"]
                is None
            )

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(
                    User.email == email
                )
            )
            database.commit()