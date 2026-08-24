import base64
import uuid

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15

from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select

from backend.app.core.config import get_settings
from backend.app.db.session import SessionLocal
from backend.app.main import app
from backend.app.models.payment_transaction import PaymentTransaction
from backend.app.models.subscription_plan import SubscriptionPlan
from backend.app.models.user import User
from backend.app.models.user_subscription import UserSubscription
from backend.app.services.payment_service import (
    create_payment_order,
)
from backend.app.services.subscription_service import (
    activate_subscription,
)


client = TestClient(app)
def create_test_alipay_key_pair():
    private_key = RSA.generate(2048)

    public_key = (
        private_key.publickey()
        .export_key()
        .decode("utf-8")
    )

    return private_key, public_key

def create_test_alipay_signature(
    data: dict[str, str],
    private_key,
) -> str:
    excluded_keys = {
        "sign",
        "sign_type",
    }

    items = [
        (key, value)
        for key, value in data.items()
        if (
            key not in excluded_keys
            and value is not None
            and value != ""
        )
    ]

    items.sort(
        key=lambda item: item[0],
    )

    content = "&".join(
        f"{key}={value}"
        for key, value in items
    )

    digest = SHA256.new(
        content.encode("utf-8"),
    )

    signature = pkcs1_15.new(
        private_key,
    ).sign(
        digest,
    )

    return base64.b64encode(
        signature
    ).decode("ascii")

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

def test_payment_success_retry_is_idempotent() -> None:
    email = (
        f"payment-idempotent-{uuid.uuid4()}@example.com"
    )
    password = "Strong-Test-Password-123!"

    provider_transaction_id = (
        f"ALI-IDEMPOTENT-{uuid.uuid4()}"
    )

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

            payment = create_payment_order(
                database,
                user_id=user.id,
                subscription_plan_id=plan.id,
                provider="alipay",
            )

            payment_id = payment.id

        first_response = client.post(
            f"/api/v1/payments/{payment_id}/success",
            headers={
                "Authorization": f"Bearer {token}",
            },
            json={
                "provider_transaction_id": (
                    provider_transaction_id
                ),
            },
        )

        assert first_response.status_code == 200
        assert first_response.json()["status"] == "success"

        with SessionLocal() as database:
            user = database.scalar(
                select(User).where(
                    User.email == email,
                )
            )

            assert user is not None

            subscription = database.scalar(
                select(UserSubscription).where(
                    UserSubscription.user_id == user.id,
                    UserSubscription.status == "active",
                )
            )

            assert subscription is not None

            subscription_id = subscription.id
            original_ends_at = subscription.ends_at

            subscription_count_before = (
                database.scalar(
                    select(
                        func.count(
                            UserSubscription.id
                        )
                    ).where(
                        UserSubscription.user_id
                        == user.id
                    )
                )
                or 0
            )

        # Retry the exact same callback.
        retry_response = client.post(
            f"/api/v1/payments/{payment_id}/success",
            headers={
                "Authorization": f"Bearer {token}",
            },
            json={
                "provider_transaction_id": (
                    provider_transaction_id
                ),
            },
        )

        assert retry_response.status_code == 200
        assert retry_response.json()["status"] == "success"
        assert (
            retry_response.json()["provider_transaction_id"]
            == provider_transaction_id
        )

        with SessionLocal() as database:
            user = database.scalar(
                select(User).where(
                    User.email == email,
                )
            )

            assert user is not None

            subscription_count_after = (
                database.scalar(
                    select(
                        func.count(
                            UserSubscription.id
                        )
                    ).where(
                        UserSubscription.user_id
                        == user.id
                    )
                )
                or 0
            )

            subscription = database.scalar(
                select(UserSubscription).where(
                    UserSubscription.id
                    == subscription_id,
                )
            )

            assert subscription is not None

            # Replay must not create or extend
            # another subscription.
            assert (
                subscription_count_after
                == subscription_count_before
            )
            assert subscription.ends_at == original_ends_at

        # Same payment, different provider transaction
        # must NOT overwrite the completed payment.
        mismatch_response = client.post(
            f"/api/v1/payments/{payment_id}/success",
            headers={
                "Authorization": f"Bearer {token}",
            },
            json={
                "provider_transaction_id": (
                    f"ALI-DIFFERENT-{uuid.uuid4()}"
                ),
            },
        )

        assert mismatch_response.status_code == 409
        assert mismatch_response.json()["detail"] == (
            "Invalid payment status"
        )

        with SessionLocal() as database:
            payment = database.scalar(
                select(PaymentTransaction).where(
                    PaymentTransaction.id == payment_id,
                )
            )

            assert payment is not None
            assert payment.status == "success"
            assert (
                payment.provider_transaction_id
                == provider_transaction_id
            )

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(
                    User.email == email,
                )
            )
            database.commit()

def test_alipay_notify_success() -> None:
    get_settings.cache_clear()

    settings = get_settings()

    private_key, public_key = create_test_alipay_key_pair()

    settings.alipay_app_id = "test-app-id"
    settings.alipay_public_key = public_key

    email = (
        f"alipay-notify-{uuid.uuid4()}@example.com"
    )
    password = "Strong-Test-Password-123!"

    try:
        client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
            },
        )

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

            payment = create_payment_order(
                database,
                user_id=user.id,
                subscription_plan_id=plan.id,
                provider="alipay",
            )

            payment_id = str(payment.id)

        payload = {
    "app_id": "test-app-id",
    "out_trade_no": payment_id,
    "trade_no": "ALI-NOTIFY-TEST-001",
    "trade_status": "TRADE_SUCCESS",
    "total_amount": "12.00",
}
        payload["sign"] = create_test_alipay_signature(
            payload,
            private_key,
        )

        response = client.post(
            "/api/v1/payments/alipay/notify",
            data=payload,
        )

        assert response.status_code == 200
        assert response.text == "success"

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(
                    User.email == email,
                )
            )
            database.commit()

def test_alipay_notify_duplicate_is_idempotent() -> None:
    get_settings.cache_clear()

    settings = get_settings()

    private_key, public_key = create_test_alipay_key_pair()

    settings.alipay_app_id = "test-app-id"
    settings.alipay_public_key = public_key

    email = (
        f"alipay-duplicate-{uuid.uuid4()}@example.com"
    )
    password = "Strong-Test-Password-123!"

    try:
        client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
            },
        )

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

            payment = create_payment_order(
                database,
                user_id=user.id,
                subscription_plan_id=plan.id,
                provider="alipay",
            )

            payment_id = str(payment.id)

        payload = {
    "app_id": "test-app-id",
    "out_trade_no": payment_id,
    "trade_no": "ALI-DUPLICATE-TEST-001",
    "trade_status": "TRADE_SUCCESS",
   "total_amount": "12.00",
}

        payload["sign"] = create_test_alipay_signature(
            payload,
            private_key,
        )

        first_response = client.post(
            "/api/v1/payments/alipay/notify",
            data=payload,
        )

        second_response = client.post(
            "/api/v1/payments/alipay/notify",
            data=payload,
        )

        assert first_response.status_code == 200
        assert first_response.text == "success"

        assert second_response.status_code == 200
        assert second_response.text == "success"

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(
                    User.email == email,
                )
            )
            database.commit()

def test_alipay_notify_rejects_wrong_app_id() -> None:
    get_settings.cache_clear()

    settings = get_settings()

    private_key, public_key = create_test_alipay_key_pair()

    settings.alipay_app_id = "test-app-id"
    settings.alipay_public_key = public_key

    email = (
        f"alipay-wrong-app-{uuid.uuid4()}@example.com"
    )
    password = "Strong-Test-Password-123!"

    try:
        client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
            },
        )

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

            payment = create_payment_order(
                database,
                user_id=user.id,
                subscription_plan_id=plan.id,
                provider="alipay",
            )

            payment_id = payment.id

        payload = {
            "app_id": "wrong-app-id",
            "out_trade_no": str(payment_id),
            "trade_no": "ALI-WRONG-APP-001",
            "trade_status": "TRADE_SUCCESS",
            "total_amount": "12.00",
        }

        payload["sign"] = create_test_alipay_signature(
            payload,
            private_key,
        )

        response = client.post(
            "/api/v1/payments/alipay/notify",
            data=payload,
        )

        assert response.status_code == 200
        assert response.text == "failure"

        with SessionLocal() as database:
            payment = database.scalar(
                select(PaymentTransaction).where(
                    PaymentTransaction.id == payment_id,
                )
            )

            assert payment is not None
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

def test_alipay_notify_rejects_wrong_amount() -> None:
    get_settings.cache_clear()

    settings = get_settings()

    private_key, public_key = create_test_alipay_key_pair()

    settings.alipay_app_id = "test-app-id"
    settings.alipay_public_key = public_key

    email = (
        f"alipay-wrong-amount-{uuid.uuid4()}@example.com"
    )
    password = "Strong-Test-Password-123!"

    try:
        client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
            },
        )

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

            payment = create_payment_order(
                database,
                user_id=user.id,
                subscription_plan_id=plan.id,
                provider="alipay",
            )

            payment_id = payment.id

        payload = {
            "app_id": "test-app-id",
            "out_trade_no": str(payment_id),
            "trade_no": "ALI-WRONG-AMOUNT-001",
            "trade_status": "TRADE_SUCCESS",

            # Actual monthly amount is 12.00 CNY.
            # This deliberately sends the wrong amount.
            "total_amount": "1.00",
        }

        payload["sign"] = create_test_alipay_signature(
            payload,
            private_key,
        )

        response = client.post(
            "/api/v1/payments/alipay/notify",
            data=payload,
        )

        assert response.status_code == 200
        assert response.text == "failure"

        with SessionLocal() as database:
            payment = database.scalar(
                select(PaymentTransaction).where(
                    PaymentTransaction.id == payment_id,
                )
            )

            assert payment is not None
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

def test_alipay_notify_rejects_failed_trade_status() -> None:
    get_settings.cache_clear()

    settings = get_settings()

    private_key, public_key = create_test_alipay_key_pair()

    settings.alipay_app_id = "test-app-id"
    settings.alipay_public_key = public_key

    email = (
        f"alipay-failed-status-{uuid.uuid4()}@example.com"
    )
    password = "Strong-Test-Password-123!"

    try:
        client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
            },
        )

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

            payment = create_payment_order(
                database,
                user_id=user.id,
                subscription_plan_id=plan.id,
                provider="alipay",
            )

            payment_id = payment.id

        payload = {
            "app_id": "test-app-id",
            "out_trade_no": str(payment_id),
            "trade_no": "ALI-FAILED-STATUS-001",
            "trade_status": "WAIT_BUYER_PAY",
            "total_amount": "12.00",
        }

        payload["sign"] = create_test_alipay_signature(
            payload,
            private_key,
        )

        response = client.post(
            "/api/v1/payments/alipay/notify",
            data=payload,
        )

        assert response.status_code == 200
        assert response.text == "failure"

        with SessionLocal() as database:
            payment = database.scalar(
                select(PaymentTransaction).where(
                    PaymentTransaction.id == payment_id,
                )
            )

            assert payment is not None
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

def test_alipay_notify_rejects_provider_mismatch() -> None:
    get_settings.cache_clear()

    settings = get_settings()

    private_key, public_key = create_test_alipay_key_pair()

    settings.alipay_app_id = "test-app-id"
    settings.alipay_public_key = public_key

    email = (
        f"alipay-provider-mismatch-{uuid.uuid4()}@example.com"
    )
    password = "Strong-Test-Password-123!"

    try:
        client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
            },
        )

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

            payment = create_payment_order(
                database,
                user_id=user.id,
                subscription_plan_id=plan.id,
                provider="wechat",
            )

            payment_id = payment.id

        payload = {
            "app_id": "test-app-id",
            "out_trade_no": str(payment_id),
            "trade_no": "ALI-PROVIDER-MISMATCH-001",
            "trade_status": "TRADE_SUCCESS",
            "total_amount": "12.00",
        }

        payload["sign"] = create_test_alipay_signature(
            payload,
            private_key,
        )

        response = client.post(
            "/api/v1/payments/alipay/notify",
            data=payload,
        )

        assert response.status_code == 200
        assert response.text == "failure"

        with SessionLocal() as database:
            payment = database.scalar(
                select(PaymentTransaction).where(
                    PaymentTransaction.id == payment_id,
                )
            )

            assert payment is not None
            assert payment.status == "pending"
            assert payment.provider == "wechat"
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

def test_alipay_notify_rejects_invalid_order_id() -> None:
    get_settings.cache_clear()

    settings = get_settings()

    private_key, public_key = create_test_alipay_key_pair()

    settings.alipay_app_id = "test-app-id"
    settings.alipay_public_key = public_key

    payload = {
        "app_id": "test-app-id",
        "out_trade_no": "not-a-valid-uuid",
        "trade_no": "ALI-BAD-ORDER-ID-001",
        "trade_status": "TRADE_SUCCESS",
        "total_amount": "12.00",
    }

    payload["sign"] = create_test_alipay_signature(
        payload,
        private_key,
    )

    response = client.post(
        "/api/v1/payments/alipay/notify",
        data=payload,
    )

    assert response.status_code == 200
    assert response.text == "failure"

def test_alipay_notify_rejects_trade_no_mismatch() -> None:
    get_settings.cache_clear()

    settings = get_settings()

    private_key, public_key = create_test_alipay_key_pair()

    settings.alipay_app_id = "test-app-id"
    settings.alipay_public_key = public_key

    email = (
        f"alipay-trade-no-mismatch-{uuid.uuid4()}@example.com"
    )
    password = "Strong-Test-Password-123!"

    try:
        client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
            },
        )

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

            payment = create_payment_order(
                database,
                user_id=user.id,
                subscription_plan_id=plan.id,
                provider="alipay",
            )

            payment_id = payment.id

        first_payload = {
            "app_id": "test-app-id",
            "out_trade_no": str(payment_id),
            "trade_no": "ALI-ORIGINAL-TRADE-001",
            "trade_status": "TRADE_SUCCESS",
            "total_amount": "12.00",
        }

        first_payload["sign"] = (
            create_test_alipay_signature(
                first_payload,
                private_key,
            )
        )

        first_response = client.post(
            "/api/v1/payments/alipay/notify",
            data=first_payload,
        )

        assert first_response.status_code == 200
        assert first_response.text == "success"

        mismatch_payload = {
            "app_id": "test-app-id",
            "out_trade_no": str(payment_id),
            "trade_no": "ALI-DIFFERENT-TRADE-002",
            "trade_status": "TRADE_SUCCESS",
            "total_amount": "12.00",
        }

        mismatch_payload["sign"] = (
            create_test_alipay_signature(
                mismatch_payload,
                private_key,
            )
        )

        mismatch_response = client.post(
            "/api/v1/payments/alipay/notify",
            data=mismatch_payload,
        )

        assert mismatch_response.status_code == 200
        assert mismatch_response.text == "failure"

        with SessionLocal() as database:
            payment = database.scalar(
                select(PaymentTransaction).where(
                    PaymentTransaction.id == payment_id,
                )
            )

            assert payment is not None
            assert payment.status == "success"
            assert (
                payment.provider_transaction_id
                == "ALI-ORIGINAL-TRADE-001"
            )

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(
                    User.email == email,
                )
            )
            database.commit()

def test_alipay_notify_rejects_tampered_signature() -> None:
    get_settings.cache_clear()

    settings = get_settings()

    private_key, public_key = create_test_alipay_key_pair()

    settings.alipay_app_id = "test-app-id"
    settings.alipay_public_key = public_key

    email = (
        f"alipay-tampered-signature-{uuid.uuid4()}@example.com"
    )
    password = "Strong-Test-Password-123!"

    try:
        client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
            },
        )

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

            payment = create_payment_order(
                database,
                user_id=user.id,
                subscription_plan_id=plan.id,
                provider="alipay",
            )

            payment_id = payment.id

        payload = {
            "app_id": "test-app-id",
            "out_trade_no": str(payment_id),
            "trade_no": "ALI-ORIGINAL-SIGNED-001",
            "trade_status": "TRADE_SUCCESS",
            "total_amount": "12.00",
        }

        payload["sign"] = create_test_alipay_signature(
            payload,
            private_key,
        )

        # Tamper with signed callback data after
        # the signature has already been generated.
        payload["trade_no"] = "ALI-TAMPERED-002"

        response = client.post(
            "/api/v1/payments/alipay/notify",
            data=payload,
        )

        assert response.status_code == 200
        assert response.text == "failure"

        with SessionLocal() as database:
            payment = database.scalar(
                select(PaymentTransaction).where(
                    PaymentTransaction.id == payment_id,
                )
            )

            assert payment is not None
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