import uuid

from sqlalchemy import delete, event, select

from backend.app.db.session import SessionLocal
from backend.app.models.subscription_plan import SubscriptionPlan
from backend.app.models.user import User
from backend.app.services.data_usage_service import record_usage
from backend.app.services.subscription_service import activate_subscription


def test_record_usage_for_active_subscription() -> None:
    email = f"usage-test-{uuid.uuid4()}@example.com"

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

            usage = record_usage(
                database,
                user_id=user.id,
                bytes_used=1024,
                record_type="download",
            )

            assert usage.user_id == user.id
            assert usage.subscription_id == subscription.id
            assert usage.bytes_used == 1024
            assert usage.record_type == "download"

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()

def test_record_usage_rejects_when_quota_exceeded() -> None:
    from backend.app.services.data_usage_service import (
        DataQuotaExceededError,
    )

    email = f"quota-test-{uuid.uuid4()}@example.com"

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

            database.refresh(subscription)

            assert subscription.data_limit_bytes is not None

            record_usage(
                database,
                user_id=user.id,
                bytes_used=subscription.data_limit_bytes,
            )

            try:
                record_usage(
                    database,
                    user_id=user.id,
                    bytes_used=1,
                )
            except DataQuotaExceededError:
                pass
            else:
                raise AssertionError(
                    "Quota exceeded usage was accepted"
                )

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()

def test_get_usage_summary_returns_current_usage() -> None:
    from backend.app.services.data_usage_service import (
        get_usage_summary,
    )

    email = f"usage-summary-{uuid.uuid4()}@example.com"

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

            assert subscription.data_limit_bytes is not None

            record_usage(
                database,
                user_id=user.id,
                bytes_used=1024,
            )

            summary = get_usage_summary(
                database,
                user_id=user.id,
            )

            assert summary["used_bytes"] == 1024
            assert summary["limit_bytes"] == (
                subscription.data_limit_bytes
            )
            assert summary["remaining_bytes"] == (
                subscription.data_limit_bytes - 1024
            )

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()

def test_record_usage_locks_active_subscription() -> None:
    email = f"usage-lock-{uuid.uuid4()}@example.com"

    executed_statements: list[str] = []

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

            bind = database.get_bind()

            def capture_statement(
                conn,
                cursor,
                statement,
                parameters,
                context,
                executemany,
            ) -> None:
                executed_statements.append(statement)

            event.listen(
                bind,
                "before_cursor_execute",
                capture_statement,
            )

            try:
                record_usage(
                    database,
                    user_id=user.id,
                    bytes_used=1024,
                    record_type="download",
                )
            finally:
                event.remove(
                    bind,
                    "before_cursor_execute",
                    capture_statement,
                )

            subscription_queries = [
                statement.upper()
                for statement in executed_statements
                if "USER_SUBSCRIPTIONS"
                in statement.upper()
            ]

            assert subscription_queries

            assert any(
                "FOR UPDATE" in statement
                for statement in subscription_queries
            )

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(
                    User.email == email,
                )
            )
            database.commit()