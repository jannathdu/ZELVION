import uuid

from sqlalchemy import delete, select

from backend.app.db.session import SessionLocal
from backend.app.models.subscription_plan import SubscriptionPlan
from backend.app.models.user import User
from backend.app.services.payment_service import (
    InvalidPaymentStatusError,
    PaymentNotFoundError,
    PlanNotFoundError,
    create_payment_order,
    get_payment_history,
    mark_payment_success,
)


def test_create_payment_order_creates_pending_payment() -> None:
    email = f"payment-test-{uuid.uuid4()}@example.com"

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

            payment = create_payment_order(
                database,
                user_id=user.id,
                subscription_plan_id=plan.id,
                provider="alipay",
            )

            assert payment.user_id == user.id
            assert payment.subscription_plan_id == plan.id
            assert payment.amount == plan.price_minor_units
            assert payment.currency == plan.currency
            assert payment.provider == "alipay"
            assert payment.status == "pending"

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()


def test_create_payment_order_rejects_invalid_plan() -> None:
    email = f"payment-invalid-{uuid.uuid4()}@example.com"

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
                create_payment_order(
                    database,
                    user_id=user.id,
                    subscription_plan_id=uuid.uuid4(),
                    provider="alipay",
                )
            except PlanNotFoundError:
                pass
            else:
                raise AssertionError(
                    "Invalid plan was accepted"
                )

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()


def test_mark_payment_success_updates_payment() -> None:
    email = f"payment-success-{uuid.uuid4()}@example.com"

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

            payment = create_payment_order(
                database,
                user_id=user.id,
                subscription_plan_id=plan.id,
                provider="alipay",
            )

            updated_payment = mark_payment_success(
                database,
                user_id=user.id,
                payment_id=payment.id,
                provider_transaction_id="ALI-TEST-001",
            )

            assert updated_payment.status == "success"
            assert (
                updated_payment.provider_transaction_id
                == "ALI-TEST-001"
            )
            assert updated_payment.paid_at is not None

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()


def test_mark_payment_success_rejects_non_pending_payment() -> None:
    email = f"payment-status-{uuid.uuid4()}@example.com"

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

            payment = create_payment_order(
                database,
                user_id=user.id,
                subscription_plan_id=plan.id,
                provider="alipay",
            )

            mark_payment_success(
                database,
                user_id=user.id,
                payment_id=payment.id,
                provider_transaction_id="ALI-TEST-002",
            )

            try:
                mark_payment_success(
                    database,
                    user_id=user.id,
                    payment_id=payment.id,
                    provider_transaction_id="ALI-TEST-003",
                )
            except InvalidPaymentStatusError:
                pass
            else:
                raise AssertionError(
                    "Non-pending payment was accepted"
                )

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()


def test_mark_payment_success_rejects_other_users_payment() -> None:
    owner_email = f"payment-owner-{uuid.uuid4()}@example.com"
    attacker_email = f"payment-other-{uuid.uuid4()}@example.com"

    try:
        with SessionLocal() as database:
            owner = User(
                email=owner_email,
                password_hash="test-only-password-hash",
            )
            other_user = User(
                email=attacker_email,
                password_hash="test-only-password-hash",
            )

            database.add_all([owner, other_user])
            database.commit()
            database.refresh(owner)
            database.refresh(other_user)

            plan = database.scalar(
                select(SubscriptionPlan).where(
                    SubscriptionPlan.code == "monthly"
                )
            )

            assert plan is not None

            payment = create_payment_order(
                database,
                user_id=owner.id,
                subscription_plan_id=plan.id,
                provider="alipay",
            )

            try:
                mark_payment_success(
                    database,
                    user_id=other_user.id,
                    payment_id=payment.id,
                    provider_transaction_id="ALI-UNAUTHORIZED",
                )
            except PaymentNotFoundError:
                pass
            else:
                raise AssertionError(
                    "Another user's payment was accepted"
                )

            database.refresh(payment)
            assert payment.status == "pending"
            assert payment.provider_transaction_id is None

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(
                    User.email.in_(
                        [owner_email, attacker_email]
                    )
                )
            )
            database.commit()


def test_get_payment_history_returns_user_payments() -> None:
    email = f"payment-history-{uuid.uuid4()}@example.com"

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

            first_payment = create_payment_order(
                database,
                user_id=user.id,
                subscription_plan_id=plan.id,
                provider="alipay",
            )

            second_payment = create_payment_order(
                database,
                user_id=user.id,
                subscription_plan_id=plan.id,
                provider="wechat",
            )

            history = get_payment_history(
                database,
                user_id=user.id,
            )

            assert len(history) == 2
            assert history[0].id == second_payment.id
            assert history[1].id == first_payment.id

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()