from decimal import Decimal

from alipay.aop.api.domain.AlipayTradePagePayModel import (
    AlipayTradePagePayModel,
)
from alipay.aop.api.request.AlipayTradePagePayRequest import (
    AlipayTradePagePayRequest,
)

from backend.app.integrations.alipay.client import (
    create_alipay_client,
)
from backend.app.integrations.alipay.config import (
    get_alipay_config,
)
from backend.app.models.payment_transaction import (
    PaymentTransaction,
)


class AlipayPaymentServiceError(Exception):
    """Base Alipay payment service error."""


def create_alipay_payment_url(
    payment: PaymentTransaction,
) -> str:
    """
    Create a signed Alipay page-payment URL
    for a pending ZELVION subscription payment.
    """

    if payment.provider != "alipay":
        raise AlipayPaymentServiceError(
            "Payment provider is not Alipay."
        )

    if payment.status != "pending":
        raise AlipayPaymentServiceError(
            "Payment is not pending."
        )

    if payment.currency != "CNY":
        raise AlipayPaymentServiceError(
            "Alipay payment currency must be CNY."
        )

    config = get_alipay_config()

    if not config.notify_url:
        raise AlipayPaymentServiceError(
            "Alipay notify URL is not configured."
        )

    client = create_alipay_client()

    total_amount = (
        Decimal(payment.amount)
        / Decimal("100")
    )

    model = AlipayTradePagePayModel()

    model.out_trade_no = str(payment.id)
    model.total_amount = f"{total_amount:.2f}"
    model.subject = "ZELVION Subscription"
    model.body = "ZELVION subscription purchase"
    model.product_code = "FAST_INSTANT_TRADE_PAY"
    model.timeout_express = "15m"

    request = AlipayTradePagePayRequest(
        biz_model=model,
    )

    request.notify_url = config.notify_url

    try:
        payment_url = client.page_execute(
            request,
            http_method="GET",
        )
    except Exception as error:
        raise AlipayPaymentServiceError(
            "Failed to create Alipay payment URL."
        ) from error

    if not payment_url:
        raise AlipayPaymentServiceError(
            "Alipay returned an empty payment URL."
        )

    return payment_url