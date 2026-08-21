from backend.app.main import app
from fastapi.testclient import TestClient


client = TestClient(app)


def test_dashboard_requires_authentication() -> None:
    response = client.get(
        "/api/v1/dashboard",
    )

    assert response.status_code == 401

def test_dashboard_returns_user_summary() -> None:
    import uuid

    from sqlalchemy import delete, select

    from backend.app.db.session import SessionLocal
    from backend.app.models.subscription_plan import SubscriptionPlan
    from backend.app.models.user import User
    from backend.app.services.device_service import (
        register_device,
    )
    from backend.app.services.payment_service import (
        create_payment_order,
    )
    from backend.app.services.subscription_service import (
        activate_subscription,
    )
    from backend.app.services.data_usage_service import (
        record_usage,
    )
    email = f"dashboard-{uuid.uuid4()}@example.com"
    password = "Strong-Test-Password-123!"

    try:
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
            },
        )
        assert register_response.status_code == 201

        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": password,
            },
        )
        assert login_response.status_code == 200

        token = login_response.json()["access_token"]

        with SessionLocal() as database:
            plan = database.scalar(
                select(SubscriptionPlan).where(
                    SubscriptionPlan.code == "monthly"
                )
            )

            user = database.scalar(
                select(User).where(
                    User.email == email
                )
            )

            assert plan is not None
            assert user is not None

            activate_subscription(
                database,
                user_id=user.id,
                plan_id=plan.id,
            )

            record_usage(
                database,
                user_id=user.id,
                bytes_used=4096,
            )

            create_payment_order(
                database,
                user_id=user.id,
                subscription_plan_id=plan.id,
                provider="alipay",
            )

            register_device(
                database,
                user_id=user.id,
                device_key_hash="test-device-key-001",
                name="Test Phone",
                platform="android",
            )

        response = client.get(
            "/api/v1/dashboard",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["user"]["email"] == email

        assert data["subscription"]["status"] == "active"

        assert data["usage"]["used_bytes"] == 4096

        assert data["devices"]["total_devices"] == 1

        assert (
            data["payments"]["last_payment_status"]
            == "pending"
        )

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()