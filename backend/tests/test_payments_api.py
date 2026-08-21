from backend.app.main import app
from fastapi.testclient import TestClient


client = TestClient(app)


def test_create_payment_requires_authentication() -> None:
    response = client.post(
        "/api/v1/payments/create",
        json={
            "subscription_plan_id": (
                "00000000-0000-0000-0000-000000000000"
            ),
            "provider": "alipay",
        },
    )

    assert response.status_code == 401

def test_create_payment_order_api() -> None:
    import uuid

    from sqlalchemy import delete, select

    from backend.app.db.session import SessionLocal
    from backend.app.models.subscription_plan import SubscriptionPlan
    from backend.app.models.user import User

    email = f"payment-api-{uuid.uuid4()}@example.com"
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

            assert plan is not None

            plan_id = str(plan.id)

        response = client.post(
            "/api/v1/payments/create",
            headers={
                "Authorization": f"Bearer {token}",
            },
            json={
                "subscription_plan_id": plan_id,
                "provider": "alipay",
            },
        )

        assert response.status_code == 201

        data = response.json()

        assert data["status"] == "pending"
        assert data["provider"] == "alipay"
        assert data["subscription_plan_id"] == plan_id

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()

def test_payment_success_api() -> None:
    import uuid

    from sqlalchemy import delete, select

    from backend.app.db.session import SessionLocal
    from backend.app.models.payment_transaction import PaymentTransaction
    from backend.app.models.subscription_plan import SubscriptionPlan
    from backend.app.models.user import User
    from backend.app.services.payment_service import (
        create_payment_order,
    )

    email = f"payment-success-api-{uuid.uuid4()}@example.com"
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

            payment = create_payment_order(
                database,
                user_id=user.id,
                subscription_plan_id=plan.id,
                provider="alipay",
            )

            payment_id = str(payment.id)

        response = client.post(
            f"/api/v1/payments/{payment_id}/success",
            headers={
                "Authorization": f"Bearer {token}",
            },
            json={
                "provider_transaction_id": "ALI-API-TEST-001",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["status"] == "success"
        assert (
            data["provider_transaction_id"]
            == "ALI-API-TEST-001"
        )
        assert data["paid_at"] is not None

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()

def test_payment_history_api() -> None:
    import uuid

    from sqlalchemy import delete, select

    from backend.app.db.session import SessionLocal
    from backend.app.models.subscription_plan import SubscriptionPlan
    from backend.app.models.user import User
    from backend.app.services.payment_service import (
        create_payment_order,
    )

    email = f"payment-history-api-{uuid.uuid4()}@example.com"
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

            create_payment_order(
                database,
                user_id=user.id,
                subscription_plan_id=plan.id,
                provider="alipay",
            )

        response = client.get(
            "/api/v1/payments/history",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert "payments" in data
        assert len(data["payments"]) == 1
        assert data["payments"][0]["provider"] == "alipay"

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()