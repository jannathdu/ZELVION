import uuid

from sqlalchemy import delete, select

from backend.app.db.session import SessionLocal
from backend.app.models.subscription_plan import SubscriptionPlan
from backend.app.models.user import User
from backend.app.services.subscription_service import (
    activate_subscription,
)


def test_activate_subscription_creates_active_entitlement() -> None:
    email = f"service-subscription-{uuid.uuid4()}@example.com"

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

            user_id = user.id
            plan_id = plan.id

            subscription = activate_subscription(
                database,
                user_id=user_id,
                plan_id=plan_id,
            )

            assert subscription.user_id == user_id
            assert subscription.plan_id == plan_id
            assert subscription.status == "active"
            assert subscription.price_minor_units == 1200
            assert subscription.currency == "CNY"
            assert subscription.duration_days == 30
            assert subscription.data_limit_bytes == 223_338_299_392
            assert subscription.max_devices == 3
            assert subscription.ends_at > subscription.starts_at

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()

def test_activate_subscription_rejects_second_active_subscription() -> None:
    from backend.app.services.subscription_service import (
        ActiveSubscriptionExistsError,
    )

    email = f"duplicate-subscription-{uuid.uuid4()}@example.com"

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

            try:
                activate_subscription(
                    database,
                    user_id=user.id,
                    plan_id=plan.id,
                )
            except ActiveSubscriptionExistsError:
                pass
            else:
                raise AssertionError(
                    "Second active subscription was not rejected"
                )

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()

def test_activate_subscription_expires_old_subscription() -> None:
    from datetime import datetime, timedelta, timezone

    from backend.app.models.user_subscription import UserSubscription

    email = f"expired-subscription-{uuid.uuid4()}@example.com"

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

            expired_subscription = UserSubscription(
                user_id=user.id,
                plan_id=plan.id,
                status="active",
                price_minor_units=plan.price_minor_units,
                currency=plan.currency,
                duration_days=plan.duration_days,
                data_limit_bytes=plan.data_limit_bytes,
                max_devices=plan.max_devices,
                starts_at=now - timedelta(days=31),
                ends_at=now - timedelta(days=1),
            )

            database.add(expired_subscription)
            database.commit()
            database.refresh(expired_subscription)

            old_subscription_id = expired_subscription.id

            new_subscription = activate_subscription(
                database,
                user_id=user.id,
                plan_id=plan.id,
                activated_at=now,
            )

            old_subscription = database.get(
                UserSubscription,
                old_subscription_id,
            )

            assert old_subscription is not None
            assert old_subscription.status == "expired"

            assert new_subscription.status == "active"
            assert new_subscription.id != old_subscription_id
            assert new_subscription.starts_at == now
            assert new_subscription.ends_at > now

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()

def test_activate_subscription_rejects_unknown_plan() -> None:
    from backend.app.services.subscription_service import (
        SubscriptionPlanUnavailableError,
    )

    email = f"unknown-plan-{uuid.uuid4()}@example.com"

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
                activate_subscription(
                    database,
                    user_id=user.id,
                    plan_id=uuid.uuid4(),
                )
            except SubscriptionPlanUnavailableError:
                pass
            else:
                raise AssertionError(
                    "Unknown subscription plan was not rejected"
                )

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()

def test_renew_subscription_extends_active_subscription() -> None:
    from datetime import timedelta

    from backend.app.services.subscription_service import (
        renew_subscription,
    )

    email = f"renew-subscription-{uuid.uuid4()}@example.com"

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

            subscription = activate_subscription(
                database,
                user_id=user.id,
                plan_id=plan.id,
            )

            original_ends_at = subscription.ends_at

            renewed_subscription = renew_subscription(
                database,
                user_id=user.id,
            )

            assert renewed_subscription.id == subscription.id
            assert renewed_subscription.status == "active"
            assert renewed_subscription.ends_at == (
                original_ends_at + timedelta(days=30)
            )

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()

def test_renew_subscription_rejects_when_none_active() -> None:
    from backend.app.services.subscription_service import (
        NoActiveSubscriptionError,
        renew_subscription,
    )

    email = f"renew-none-{uuid.uuid4()}@example.com"

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
                renew_subscription(
                    database,
                    user_id=user.id,
                )
            except NoActiveSubscriptionError:
                pass
            else:
                raise AssertionError(
                    "Renewal without an active subscription was not rejected"
                )

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()

def test_renew_subscription_marks_expired_subscription() -> None:
    from datetime import datetime, timedelta, timezone

    from backend.app.models.user_subscription import UserSubscription
    from backend.app.services.subscription_service import (
        NoActiveSubscriptionError,
        renew_subscription,
    )

    email = f"renew-expired-{uuid.uuid4()}@example.com"

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

            subscription = UserSubscription(
                user_id=user.id,
                plan_id=plan.id,
                status="active",
                price_minor_units=plan.price_minor_units,
                currency=plan.currency,
                duration_days=plan.duration_days,
                data_limit_bytes=plan.data_limit_bytes,
                max_devices=plan.max_devices,
                starts_at=now - timedelta(days=31),
                ends_at=now - timedelta(days=1),
            )

            database.add(subscription)
            database.commit()
            database.refresh(subscription)

            subscription_id = subscription.id

            try:
                renew_subscription(
                    database,
                    user_id=user.id,
                    renewed_at=now,
                )
            except NoActiveSubscriptionError:
                pass
            else:
                raise AssertionError(
                    "Expired subscription was incorrectly renewed"
                )

            stored_subscription = database.get(
                UserSubscription,
                subscription_id,
            )

            assert stored_subscription is not None
            assert stored_subscription.status == "expired"

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()

def test_expire_due_subscriptions_marks_elapsed_active_rows() -> None:
    from datetime import datetime, timedelta, timezone

    from backend.app.models.user_subscription import UserSubscription
    from backend.app.services.subscription_service import (
        expire_due_subscriptions,
    )

    email = f"expire-due-{uuid.uuid4()}@example.com"

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

            subscription = UserSubscription(
                user_id=user.id,
                plan_id=plan.id,
                status="active",
                price_minor_units=plan.price_minor_units,
                currency=plan.currency,
                duration_days=plan.duration_days,
                data_limit_bytes=plan.data_limit_bytes,
                max_devices=plan.max_devices,
                starts_at=now - timedelta(days=31),
                ends_at=now - timedelta(days=1),
            )

            database.add(subscription)
            database.commit()
            database.refresh(subscription)

            subscription_id = subscription.id

            expired_count = expire_due_subscriptions(
                database,
                expired_at=now,
            )

            stored_subscription = database.get(
                UserSubscription,
                subscription_id,
            )

            assert expired_count >= 1
            assert stored_subscription is not None
            assert stored_subscription.status == "expired"

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()