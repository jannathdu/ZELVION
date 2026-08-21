id="device_test_1"
import uuid

from sqlalchemy import delete, select

from backend.app.db.session import SessionLocal
from backend.app.models.subscription_plan import SubscriptionPlan
from backend.app.models.user import User
from backend.app.services.device_service import register_device
from backend.app.services.subscription_service import activate_subscription


def test_register_device_for_active_subscriber() -> None:
    email = f"device-test-{uuid.uuid4()}@example.com"

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

            device = register_device(
                database,
                user_id=user.id,
                device_key_hash="device-hash-001",
                name="My Laptop",
                platform="windows",
            )

            assert device.user_id == user.id
            assert device.device_key_hash == "device-hash-001"
            assert device.name == "My Laptop"
            assert device.platform == "windows"
            assert device.is_active is True

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()

def test_register_device_rejects_when_device_limit_reached() -> None:
    from backend.app.services.device_service import (
        DeviceLimitReachedError,
    )

    email = f"device-limit-{uuid.uuid4()}@example.com"

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

            for index in range(3):
                register_device(
                    database,
                    user_id=user.id,
                    device_key_hash=f"device-limit-{index}",
                    name=f"Device {index}",
                    platform="test",
                )

            try:
                register_device(
                    database,
                    user_id=user.id,
                    device_key_hash="device-limit-4",
                    name="Fourth Device",
                    platform="test",
                )
            except DeviceLimitReachedError:
                pass
            else:
                raise AssertionError(
                    "Device limit was not enforced"
                )

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()

def test_register_device_rejects_duplicate_device() -> None:
    from backend.app.services.device_service import (
        DuplicateDeviceError,
    )

    email = f"device-duplicate-{uuid.uuid4()}@example.com"

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

            register_device(
                database,
                user_id=user.id,
                device_key_hash="same-device-hash",
                name="Primary Device",
                platform="android",
            )

            try:
                register_device(
                    database,
                    user_id=user.id,
                    device_key_hash="same-device-hash",
                    name="Duplicate Device",
                    platform="android",
                )
            except DuplicateDeviceError:
                pass
            else:
                raise AssertionError(
                    "Duplicate device was not rejected"
                )

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()

def test_register_device_requires_active_subscription() -> None:
    from backend.app.services.device_service import (
        NoActiveSubscriptionError,
    )

    email = f"device-no-sub-{uuid.uuid4()}@example.com"

    try:
        with SessionLocal() as database:
            user = User(
                email=email,
                password_hash="test-only-password-hash",
            )
            database.add(user)
            database.commit()
            database.refresh(user)

            try:
                register_device(
                    database,
                    user_id=user.id,
                    device_key_hash="no-sub-device",
                    name="No Subscription Device",
                    platform="test",
                )
            except NoActiveSubscriptionError:
                pass
            else:
                raise AssertionError(
                    "Device registration without subscription was allowed"
                )

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()

def test_revoke_device_deactivates_device() -> None:
    from backend.app.services.device_service import revoke_device

    email = f"device-revoke-{uuid.uuid4()}@example.com"

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

            device = register_device(
                database,
                user_id=user.id,
                device_key_hash="revoke-device-001",
                name="Revoke Test Device",
                platform="test",
            )

            revoked_device = revoke_device(
                database,
                user_id=user.id,
                device_id=device.id,
            )

            assert revoked_device.id == device.id
            assert revoked_device.is_active is False
            assert revoked_device.revoked_at is not None

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()

def test_list_user_devices_returns_user_devices() -> None:
    from backend.app.services.device_service import list_user_devices

    email = f"device-list-{uuid.uuid4()}@example.com"

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

            first_device = register_device(
                database,
                user_id=user.id,
                device_key_hash="list-device-001",
                name="Laptop",
                platform="windows",
            )

            second_device = register_device(
                database,
                user_id=user.id,
                device_key_hash="list-device-002",
                name="Phone",
                platform="android",
            )

            devices = list_user_devices(
                database,
                user_id=user.id,
            )

            assert len(devices) == 2
            assert devices[0].id in {
                first_device.id,
                second_device.id,
            }
            assert devices[1].id in {
                first_device.id,
                second_device.id,
            }

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()