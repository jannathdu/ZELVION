from backend.app.main import app
from fastapi.testclient import TestClient


client = TestClient(app)


def test_create_device_requires_authentication() -> None:
    response = client.post(
        "/api/v1/devices",
        json={
            "device_key_hash": "test-device",
            "name": "Test Device",
            "platform": "test",
        },
    )

    assert response.status_code == 401

def test_create_device_for_subscriber() -> None:
    import uuid

    from sqlalchemy import delete, select

    from backend.app.db.session import SessionLocal
    from backend.app.models.subscription_plan import SubscriptionPlan
    from backend.app.models.user import User

    email = f"device-api-{uuid.uuid4()}@example.com"
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

            from backend.app.services.subscription_service import (
                activate_subscription,
            )

            user = database.scalar(
                select(User).where(
                    User.email == email
                )
            )

            assert user is not None

            activate_subscription(
                database,
                user_id=user.id,
                plan_id=plan.id,
            )

        response = client.post(
            "/api/v1/devices",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
            json={
                "device_key_hash": "api-device-001",
                "name": "My Laptop",
                "platform": "windows",
            },
        )

        assert response.status_code == 201

        data = response.json()

        assert data["device_key_hash"] == "api-device-001"
        assert data["name"] == "My Laptop"
        assert data["platform"] == "windows"
        assert data["is_active"] is True

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()

def test_create_device_requires_active_subscription() -> None:
    import uuid

    from sqlalchemy import delete

    from backend.app.db.session import SessionLocal
    from backend.app.models.user import User

    email = f"device-api-no-sub-{uuid.uuid4()}@example.com"
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
            "/api/v1/devices",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
            json={
                "device_key_hash": "no-sub-device",
                "name": "No Subscription Device",
                "platform": "test",
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

def test_create_device_rejects_after_max_devices() -> None:
    import uuid

    from sqlalchemy import delete, select

    from backend.app.db.session import SessionLocal
    from backend.app.models.subscription_plan import SubscriptionPlan
    from backend.app.models.user import User
    from backend.app.services.subscription_service import (
        activate_subscription,
    )

    email = f"device-api-limit-{uuid.uuid4()}@example.com"
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

        headers = {
            "Authorization": f"Bearer {access_token}",
        }

        for index in range(3):
            response = client.post(
                "/api/v1/devices",
                headers=headers,
                json={
                    "device_key_hash": f"limit-device-{index}",
                    "name": f"Device {index}",
                    "platform": "test",
                },
            )

            assert response.status_code == 201

        response = client.post(
            "/api/v1/devices",
            headers=headers,
            json={
                "device_key_hash": "limit-device-4",
                "name": "Fourth Device",
                "platform": "test",
            },
        )

        assert response.status_code == 409
        assert response.json()["detail"] == (
            "Device limit reached"
        )

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()

def test_create_device_rejects_duplicate_device() -> None:
    import uuid

    from sqlalchemy import delete, select

    from backend.app.db.session import SessionLocal
    from backend.app.models.subscription_plan import SubscriptionPlan
    from backend.app.models.user import User
    from backend.app.services.subscription_service import (
        activate_subscription,
    )

    email = f"device-api-duplicate-{uuid.uuid4()}@example.com"
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

        headers = {
            "Authorization": f"Bearer {access_token}",
        }

        payload = {
            "device_key_hash": "duplicate-api-device",
            "name": "Primary Device",
            "platform": "android",
        }

        first_response = client.post(
            "/api/v1/devices",
            headers=headers,
            json=payload,
        )

        assert first_response.status_code == 201

        second_response = client.post(
            "/api/v1/devices",
            headers=headers,
            json=payload,
        )

        assert second_response.status_code == 409
        assert second_response.json()["detail"] == (
            "Device already exists"
        )

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()

def test_revoke_device_api() -> None:
    import uuid

    from sqlalchemy import delete, select

    from backend.app.db.session import SessionLocal
    from backend.app.models.subscription_plan import SubscriptionPlan
    from backend.app.models.user import User
    from backend.app.services.subscription_service import (
        activate_subscription,
    )

    email = f"device-api-revoke-{uuid.uuid4()}@example.com"
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
            "/api/v1/devices",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
            json={
                "device_key_hash": "revoke-api-device",
                "name": "Revoke Device",
                "platform": "android",
            },
        )

        assert response.status_code == 201

        device_id = response.json()["id"]

        delete_response = client.delete(
            f"/api/v1/devices/{device_id}",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
        )

        assert delete_response.status_code == 200

        data = delete_response.json()

        assert data["id"] == device_id
        assert data["is_active"] is False
        assert data["revoked_at"] is not None

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()

def test_get_my_devices_api() -> None:
    import uuid

    from sqlalchemy import delete, select

    from backend.app.db.session import SessionLocal
    from backend.app.models.subscription_plan import SubscriptionPlan
    from backend.app.models.user import User
    from backend.app.services.subscription_service import (
        activate_subscription,
    )

    email = f"device-api-list-{uuid.uuid4()}@example.com"
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

        headers = {
            "Authorization": f"Bearer {access_token}",
        }

        create_response = client.post(
            "/api/v1/devices",
            headers=headers,
            json={
                "device_key_hash": "list-api-device",
                "name": "List Device",
                "platform": "android",
            },
        )

        assert create_response.status_code == 201

        response = client.get(
            "/api/v1/devices",
            headers=headers,
        )

        assert response.status_code == 200

        devices = response.json()

        assert len(devices) == 1
        assert devices[0]["device_key_hash"] == (
            "list-api-device"
        )

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()