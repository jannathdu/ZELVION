from backend.app.main import app
from fastapi.testclient import TestClient


client = TestClient(app)


def test_create_usage_requires_authentication() -> None:
    response = client.post(
        "/api/v1/usage",
        json={
            "bytes_used": 1024,
            "record_type": "download",
        },
    )

    assert response.status_code == 401

def test_create_usage_for_subscriber() -> None:
    import uuid

    from sqlalchemy import delete, select

    from backend.app.db.session import SessionLocal
    from backend.app.models.subscription_plan import SubscriptionPlan
    from backend.app.models.user import User
    from backend.app.services.subscription_service import (
        activate_subscription,
    )

    email = f"usage-api-{uuid.uuid4()}@example.com"
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

        access_token = login_response.json()["access_token"]

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

        response = client.post(
            "/api/v1/usage",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
            json={
                "bytes_used": 2048,
                "record_type": "download",
            },
        )

        assert response.status_code == 201

        data = response.json()

        assert data["bytes_used"] == 2048
        assert data["record_type"] == "download"

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()

def test_create_usage_requires_subscription() -> None:
    import uuid

    from sqlalchemy import delete

    from backend.app.db.session import SessionLocal
    from backend.app.models.user import User

    email = f"usage-api-no-sub-{uuid.uuid4()}@example.com"
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

        access_token = login_response.json()["access_token"]

        response = client.post(
            "/api/v1/usage",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
            json={
                "bytes_used": 1024,
                "record_type": "download",
            },
        )

        assert response.status_code == 403
        assert response.json()["detail"] == (
            "Active subscription required"
        )

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()

def test_create_usage_rejects_when_quota_exceeded() -> None:
    import uuid

    from sqlalchemy import delete, select

    from backend.app.db.session import SessionLocal
    from backend.app.models.subscription_plan import SubscriptionPlan
    from backend.app.models.user import User
    from backend.app.services.subscription_service import (
        activate_subscription,
    )

    email = f"usage-api-quota-{uuid.uuid4()}@example.com"
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

        access_token = login_response.json()["access_token"]

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

            subscription = activate_subscription(
                database,
                user_id=user.id,
                plan_id=plan.id,
            )

            assert subscription.data_limit_bytes is not None

            limit = subscription.data_limit_bytes

        headers = {
            "Authorization": f"Bearer {access_token}",
        }

        first_response = client.post(
            "/api/v1/usage",
            headers=headers,
            json={
                "bytes_used": limit,
                "record_type": "download",
            },
        )

        assert first_response.status_code == 201

        second_response = client.post(
            "/api/v1/usage",
            headers=headers,
            json={
                "bytes_used": 1,
                "record_type": "download",
            },
        )

        assert second_response.status_code == 409
        assert second_response.json()["detail"] == (
            "Data quota exceeded"
        )

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()

def test_get_usage_summary_api() -> None:
    import uuid

    from sqlalchemy import delete, select

    from backend.app.db.session import SessionLocal
    from backend.app.models.subscription_plan import SubscriptionPlan
    from backend.app.models.user import User
    from backend.app.services.subscription_service import (
        activate_subscription,
    )

    email = f"usage-api-summary-{uuid.uuid4()}@example.com"
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

        access_token = login_response.json()["access_token"]

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

            subscription = activate_subscription(
                database,
                user_id=user.id,
                plan_id=plan.id,
            )

            assert subscription.data_limit_bytes is not None

        headers = {
            "Authorization": f"Bearer {access_token}",
        }

        create_response = client.post(
            "/api/v1/usage",
            headers=headers,
            json={
                "bytes_used": 4096,
                "record_type": "download",
            },
        )

        assert create_response.status_code == 201

        response = client.get(
            "/api/v1/usage/summary",
            headers=headers,
        )

        assert response.status_code == 200

        data = response.json()

        assert data["used_bytes"] == 4096
        assert data["limit_bytes"] is not None
        assert data["remaining_bytes"] == (
            data["limit_bytes"] - 4096
        )

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()