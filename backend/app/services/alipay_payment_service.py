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
    Create Alipay payment URL for a pending payment.
    """

    client = create_alipay_client()
    config = get_alipay_config()

    order_string = (
        client.api_alipay_trade_page_pay(
            out_trade_no=str(payment.id),
            total_amount=(
                f"{payment.amount / 100:.2f}"
            ),
            subject=(
                "ZELVION Subscription"
            ),
            return_url=None,
        )
    )

    return (
        f"{config.gateway_url}?{order_string}"
    )