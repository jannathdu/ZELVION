from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_list_active_subscription_plans() -> None:
    response = client.get("/api/v1/subscriptions/plans")

    assert response.status_code == 200

    plans = response.json()
    plans_by_code = {
        plan["code"]: plan
        for plan in plans
    }

    assert {"day-pass", "monthly"}.issubset(
        plans_by_code
    )

    day_pass = plans_by_code["day-pass"]
    assert day_pass["price_minor_units"] == 100
    assert day_pass["currency"] == "CNY"
    assert day_pass["duration_days"] == 1
    assert day_pass["data_limit_bytes"] == 10_737_418_240
    assert day_pass["max_devices"] == 1

    monthly = plans_by_code["monthly"]
    assert monthly["price_minor_units"] == 1200
    assert monthly["currency"] == "CNY"
    assert monthly["duration_days"] == 30
    assert monthly["data_limit_bytes"] == 223_338_299_392
    assert monthly["max_devices"] == 3

    prices = [
        plan["price_minor_units"]
        for plan in plans
    ]
    assert prices == sorted(prices)

def test_my_subscription_requires_authentication() -> None:
    response = client.get("/api/v1/subscriptions/me")

    assert response.status_code == 401

def test_my_subscription_returns_none_when_inactive() -> None:
    import uuid

    from sqlalchemy import delete

    from backend.app.db.session import SessionLocal
    from backend.app.models.user import User

    email = f"subscription-test-{uuid.uuid4()}@example.com"
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

        response = client.get(
            "/api/v1/subscriptions/me",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
        )

        assert response.status_code == 200
        assert response.json() is None

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()

def test_my_subscription_returns_active_subscription() -> None:
    import uuid
    from datetime import datetime, timedelta, timezone

    from sqlalchemy import delete, select

    from backend.app.db.session import SessionLocal
    from backend.app.models.subscription_plan import SubscriptionPlan
    from backend.app.models.user import User
    from backend.app.models.user_subscription import UserSubscription

    email = f"active-subscription-{uuid.uuid4()}@example.com"
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
            user = database.scalar(
                select(User).where(User.email == email)
            )
            plan = database.scalar(
                select(SubscriptionPlan).where(
                    SubscriptionPlan.code == "monthly"
                )
            )

            assert user is not None
            assert plan is not None

            starts_at = datetime.now(timezone.utc)
            ends_at = starts_at + timedelta(
                days=plan.duration_days
            )

            subscription = UserSubscription(
                user_id=user.id,
                plan_id=plan.id,
                status="active",
                price_minor_units=plan.price_minor_units,
                currency=plan.currency,
                duration_days=plan.duration_days,
                data_limit_bytes=plan.data_limit_bytes,
                max_devices=plan.max_devices,
                starts_at=starts_at,
                ends_at=ends_at,
            )

            database.add(subscription)
            database.commit()

        response = client.get(
            "/api/v1/subscriptions/me",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data is not None
        assert data["status"] == "active"
        assert data["plan_id"] == str(plan.id)
        assert data["price_minor_units"] == 1200
        assert data["currency"] == "CNY"
        assert data["duration_days"] == 30
        assert data["max_devices"] == 3

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()

def test_my_subscription_returns_active_subscription() -> None:
    import uuid
    from datetime import datetime, timedelta, timezone

    from sqlalchemy import delete, select

    from backend.app.db.session import SessionLocal
    from backend.app.models.subscription_plan import SubscriptionPlan
    from backend.app.models.user import User
    from backend.app.models.user_subscription import UserSubscription

    email = f"active-subscription-{uuid.uuid4()}@example.com"
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
            user = database.scalar(
                select(User).where(User.email == email)
            )
            plan = database.scalar(
                select(SubscriptionPlan).where(
                    SubscriptionPlan.code == "monthly"
                )
            )

            assert user is not None
            assert plan is not None

            plan_id = plan.id
            starts_at = datetime.now(timezone.utc)
            ends_at = starts_at + timedelta(
                days=plan.duration_days
            )

            database.add(
                UserSubscription(
                    user_id=user.id,
                    plan_id=plan.id,
                    status="active",
                    price_minor_units=plan.price_minor_units,
                    currency=plan.currency,
                    duration_days=plan.duration_days,
                    data_limit_bytes=plan.data_limit_bytes,
                    max_devices=plan.max_devices,
                    starts_at=starts_at,
                    ends_at=ends_at,
                )
            )
            database.commit()

        response = client.get(
            "/api/v1/subscriptions/me",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data is not None
        assert data["status"] == "active"
        assert data["plan_id"] == str(plan_id)
        assert data["price_minor_units"] == 1200
        assert data["currency"] == "CNY"
        assert data["duration_days"] == 30
        assert data["max_devices"] == 3

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()

def test_mock_activation_requires_authentication() -> None:
    response = client.post(
        "/api/v1/subscriptions/mock-activate",
        json={
            "plan_id": "00000000-0000-0000-0000-000000000001",
        },
    )

    assert response.status_code == 401

def test_mock_activation_creates_subscription() -> None:
    import uuid

    from sqlalchemy import delete, select

    from backend.app.db.session import SessionLocal
    from backend.app.models.subscription_plan import SubscriptionPlan
    from backend.app.models.user import User

    email = f"mock-activation-{uuid.uuid4()}@example.com"
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

            assert plan is not None
            plan_id = plan.id

        response = client.post(
            "/api/v1/subscriptions/mock-activate",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
            json={
                "plan_id": str(plan_id),
            },
        )

        assert response.status_code == 201

        data = response.json()

        assert data["plan_id"] == str(plan_id)
        assert data["status"] == "active"
        assert data["price_minor_units"] == 1200
        assert data["currency"] == "CNY"
        assert data["duration_days"] == 30
        assert data["max_devices"] == 3

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()

def test_mock_activation_rejects_second_active_subscription() -> None:
    import uuid

    from sqlalchemy import delete, select

    from backend.app.db.session import SessionLocal
    from backend.app.models.subscription_plan import SubscriptionPlan
    from backend.app.models.user import User

    email = f"mock-duplicate-{uuid.uuid4()}@example.com"
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

            assert plan is not None
            plan_id = plan.id

        headers = {
            "Authorization": f"Bearer {access_token}",
        }
        payload = {
            "plan_id": str(plan_id),
        }

        first_response = client.post(
            "/api/v1/subscriptions/mock-activate",
            headers=headers,
            json=payload,
        )
        assert first_response.status_code == 201

        second_response = client.post(
            "/api/v1/subscriptions/mock-activate",
            headers=headers,
            json=payload,
        )

        assert second_response.status_code == 409
        assert second_response.json()["detail"] == (
            "An active subscription already exists"
        )

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()

def test_mock_activation_is_hidden_when_disabled(
    monkeypatch,
) -> None:
    import uuid
    from types import SimpleNamespace

    from sqlalchemy import delete

    from backend.app.db.session import SessionLocal
    from backend.app.models.user import User

    email = f"mock-disabled-{uuid.uuid4()}@example.com"
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

        monkeypatch.setattr(
            "backend.app.api.v1.subscriptions.get_settings",
            lambda: SimpleNamespace(
                enable_mock_subscription_activation=False,
            ),
        )

        response = client.post(
            "/api/v1/subscriptions/mock-activate",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
            json={
                "plan_id": str(uuid.uuid4()),
            },
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Not found"

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()

def test_mock_renewal_requires_authentication() -> None:
    response = client.post(
        "/api/v1/subscriptions/mock-renew"
    )

    assert response.status_code == 401

def test_mock_renewal_extends_active_subscription() -> None:
    import uuid
    from datetime import datetime

    from sqlalchemy import delete, select

    from backend.app.db.session import SessionLocal
    from backend.app.models.subscription_plan import SubscriptionPlan
    from backend.app.models.user import User

    email = f"mock-renew-{uuid.uuid4()}@example.com"
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
        headers = {
            "Authorization": f"Bearer {access_token}",
        }

        with SessionLocal() as database:
            plan = database.scalar(
                select(SubscriptionPlan).where(
                    SubscriptionPlan.code == "monthly"
                )
            )

            assert plan is not None
            plan_id = plan.id

        activation_response = client.post(
            "/api/v1/subscriptions/mock-activate",
            headers=headers,
            json={
                "plan_id": str(plan_id),
            },
        )

        assert activation_response.status_code == 201

        original_ends_at = datetime.fromisoformat(
            activation_response.json()["ends_at"]
        )

        renewal_response = client.post(
            "/api/v1/subscriptions/mock-renew",
            headers=headers,
        )

        assert renewal_response.status_code == 200

        renewed_ends_at = datetime.fromisoformat(
            renewal_response.json()["ends_at"]
        )

        assert renewed_ends_at > original_ends_at
        assert renewal_response.json()["status"] == "active"

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()

def test_mock_renewal_rejects_when_none_active() -> None:
    import uuid

    from sqlalchemy import delete

    from backend.app.db.session import SessionLocal
    from backend.app.models.user import User

    email = f"mock-renew-none-{uuid.uuid4()}@example.com"
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
            "/api/v1/subscriptions/mock-renew",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
        )

        assert response.status_code == 409
        assert response.json()["detail"] == (
            "No active subscription to renew"
        )

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()

def test_mock_renewal_is_hidden_when_disabled(
    monkeypatch,
) -> None:
    import uuid
    from types import SimpleNamespace

    from sqlalchemy import delete

    from backend.app.db.session import SessionLocal
    from backend.app.models.user import User

    email = f"mock-renew-disabled-{uuid.uuid4()}@example.com"
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

        monkeypatch.setattr(
            "backend.app.api.v1.subscriptions.get_settings",
            lambda: SimpleNamespace(
                enable_mock_subscription_activation=False,
            ),
        )

        response = client.post(
            "/api/v1/subscriptions/mock-renew",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Not found"

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()