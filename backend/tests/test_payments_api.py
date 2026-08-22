import uuid

from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select

from backend.app.db.session import SessionLocal
from backend.app.main import app
from backend.app.models.payment_transaction import PaymentTransaction
from backend.app.models.subscription_plan import SubscriptionPlan
from backend.app.models.user import User
from backend.app.services.payment_service import (
    create_payment_order,
)
from backend.app.services.subscription_service import (
    activate_subscription,
)


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
                delete(User).where(
                    User.email == email,
                )
            )
            database.commit()


def test_payment_success_api() -> None:
    email = (
        f"payment-success-api-{uuid.uuid4()}@example.com"
    )
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
                    User.email == email,
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
                "provider_transaction_id": (
                    "ALI-API-TEST-001"
                ),
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
                delete(User).where(
                    User.email == email,
                )
            )
            database.commit()


def test_payment_history_api() -> None:
    email = (
        f"payment-history-api-{uuid.uuid4()}@example.com"
    )
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
                    User.email == email,
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
        assert (
            data["payments"][0]["provider"]
            == "alipay"
        )

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(
                    User.email == email,
                )
            )
            database.commit()


def test_create_payment_rejects_active_subscription() -> None:
    email = (
        f"payment-active-sub-{uuid.uuid4()}@example.com"
    )
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
            user = database.scalar(
                select(User).where(
                    User.email == email,
                )
            )

            plan = database.scalar(
                select(SubscriptionPlan).where(
                    SubscriptionPlan.code == "monthly"
                )
            )

            assert user is not None
            assert plan is not None

            activate_subscription(
                database,
                user_id=user.id,
                plan_id=plan.id,
            )

            plan_id = str(plan.id)

            payment_count_before = (
                database.scalar(
                    select(
                        func.count(
                            PaymentTransaction.id
                        )
                    ).where(
                        PaymentTransaction.user_id
                        == user.id
                    )
                )
                or 0
            )

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

        assert response.status_code == 409

        assert response.json()["detail"] == (
            "An active subscription already exists"
        )

        with SessionLocal() as database:
            user = database.scalar(
                select(User).where(
                    User.email == email,
                )
            )

            assert user is not None

            payment_count_after = (
                database.scalar(
                    select(
                        func.count(
                            PaymentTransaction.id
                        )
                    ).where(
                        PaymentTransaction.user_id
                        == user.id
                    )
                )
                or 0
            )

            assert (
                payment_count_after
                == payment_count_before
            )

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(
                    User.email == email,
                )
            )
            database.commit()

def test_payment_success_rolls_back_if_subscription_activation_fails() -> None:
    import uuid

    from sqlalchemy import delete, select

    from backend.app.db.session import SessionLocal
    from backend.app.models.payment_transaction import (
        PaymentTransaction,
    )
    from backend.app.models.subscription_plan import (
        SubscriptionPlan,
    )
    from backend.app.models.user import User
    from backend.app.services.payment_service import (
        create_payment_order,
    )
    from backend.app.services.subscription_service import (
        activate_subscription,
    )

    email = (
        f"payment-atomic-{uuid.uuid4()}@example.com"
    )
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
            user = database.scalar(
                select(User).where(
                    User.email == email,
                )
            )

            plan = database.scalar(
                select(SubscriptionPlan).where(
                    SubscriptionPlan.code == "monthly",
                )
            )

            assert user is not None
            assert plan is not None

            payment = create_payment_order(
                database,
                user_id=user.id,
                subscription_plan_id=plan.id,
                provider="alipay",
            )

            payment_id = payment.id

            # Create an active subscription AFTER the
            # pending payment exists. This forces the
            # success endpoint's activation step to fail.
            activate_subscription(
                database,
                user_id=user.id,
                plan_id=plan.id,
            )

        response = client.post(
            f"/api/v1/payments/{payment_id}/success",
            headers={
                "Authorization": f"Bearer {token}",
            },
            json={
                "provider_transaction_id": (
                    f"ATOMIC-{uuid.uuid4()}"
                ),
            },
        )

        assert response.status_code == 409

        with SessionLocal() as database:
            payment = database.scalar(
                select(PaymentTransaction).where(
                    PaymentTransaction.id == payment_id,
                )
            )

            assert payment is not None

            # Critical atomicity assertions:
            assert payment.status == "pending"
            assert payment.provider_transaction_id is None
            assert payment.paid_at is None

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(
                    User.email == email,
                )
            )
            database.commit()