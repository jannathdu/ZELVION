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

            create_payment_order(
                database,
                user_id=user.id,
                subscription_plan_id=plan.id,
                provider="alipay",
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
                dashboard["usage"]["used_bytes"]
                == 8192
            )

            assert (
                dashboard["devices"]["total_devices"]
                == 1
            )

            assert (
                dashboard["payments"]["last_payment_status"]
                == "pending"
            )

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()