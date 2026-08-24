import uuid
from types import SimpleNamespace

import pytest

from backend.app.models.payment_transaction import (
    PaymentTransaction,
)
from backend.app.services import alipay_payment_service
from backend.app.services.alipay_payment_service import (
    AlipayPaymentServiceError,
)


def build_payment(
    *,
    provider: str = "alipay",
    status: str = "pending",
    currency: str = "CNY",
    amount: int = 1200,
) -> PaymentTransaction:
    return PaymentTransaction(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        subscription_plan_id=uuid.uuid4(),
        amount=amount,
        currency=currency,
        provider=provider,
        status=status,
    )


def test_create_alipay_payment_url_builds_correct_request(
    monkeypatch,
) -> None:
    payment = build_payment()

    captured: dict[str, object] = {}

    class FakeAlipayClient:
        def page_execute(
            self,
            request,
            http_method="POST",
        ) -> str:
            captured["request"] = request
            captured["http_method"] = http_method

            return (
                "https://openapi-sandbox.dl.alipaydev.com/"
                "gateway.do?mock_signed_order=1"
            )

    fake_config = SimpleNamespace(
        notify_url=(
            "https://example.com/"
            "api/v1/payments/alipay/notify"
        ),
    )

    monkeypatch.setattr(
        alipay_payment_service,
        "create_alipay_client",
        lambda: FakeAlipayClient(),
    )

    monkeypatch.setattr(
        alipay_payment_service,
        "get_alipay_config",
        lambda: fake_config,
    )

    payment_url = (
        alipay_payment_service.create_alipay_payment_url(
            payment,
        )
    )

    assert (
        payment_url
        == (
            "https://openapi-sandbox.dl.alipaydev.com/"
            "gateway.do?mock_signed_order=1"
        )
    )

    assert captured["http_method"] == "GET"

    request = captured["request"]

    assert request.notify_url == fake_config.notify_url

    model = request.biz_model

    assert model.out_trade_no == str(payment.id)
    assert model.total_amount == "12.00"
    assert model.subject == "ZELVION Subscription"
    assert model.body == "ZELVION subscription purchase"

    assert (
        model.product_code
        == "FAST_INSTANT_TRADE_PAY"
    )

    assert model.timeout_express == "15m"


def test_create_alipay_payment_url_rejects_wrong_provider() -> None:
    payment = build_payment(
        provider="wechat",
    )

    with pytest.raises(
        AlipayPaymentServiceError,
        match="Payment provider is not Alipay",
    ):
        alipay_payment_service.create_alipay_payment_url(
            payment,
        )


def test_create_alipay_payment_url_rejects_non_pending() -> None:
    payment = build_payment(
        status="success",
    )

    with pytest.raises(
        AlipayPaymentServiceError,
        match="Payment is not pending",
    ):
        alipay_payment_service.create_alipay_payment_url(
            payment,
        )


def test_create_alipay_payment_url_rejects_non_cny() -> None:
    payment = build_payment(
        currency="USD",
    )

    with pytest.raises(
        AlipayPaymentServiceError,
        match="Alipay payment currency must be CNY",
    ):
        alipay_payment_service.create_alipay_payment_url(
            payment,
        )


def test_create_alipay_payment_url_requires_notify_url(
    monkeypatch,
) -> None:
    payment = build_payment()

    fake_config = SimpleNamespace(
        notify_url=None,
    )

    monkeypatch.setattr(
        alipay_payment_service,
        "get_alipay_config",
        lambda: fake_config,
    )

    with pytest.raises(
        AlipayPaymentServiceError,
        match="Alipay notify URL is not configured",
    ):
        alipay_payment_service.create_alipay_payment_url(
            payment,
        )


def test_create_alipay_payment_url_handles_sdk_failure(
    monkeypatch,
) -> None:
    payment = build_payment()

    class FailingAlipayClient:
        def page_execute(
            self,
            request,
            http_method="POST",
        ) -> str:
            raise RuntimeError(
                "Simulated Alipay SDK failure"
            )

    fake_config = SimpleNamespace(
        notify_url=(
            "https://example.com/"
            "api/v1/payments/alipay/notify"
        ),
    )

    monkeypatch.setattr(
        alipay_payment_service,
        "get_alipay_config",
        lambda: fake_config,
    )

    monkeypatch.setattr(
        alipay_payment_service,
        "create_alipay_client",
        lambda: FailingAlipayClient(),
    )

    with pytest.raises(
        AlipayPaymentServiceError,
        match="Failed to create Alipay payment URL",
    ):
        alipay_payment_service.create_alipay_payment_url(
            payment,
        )