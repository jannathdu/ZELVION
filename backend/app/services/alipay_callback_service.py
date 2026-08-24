import uuid
from decimal import Decimal, InvalidOperation

from sqlalchemy.orm import Session

from backend.app.integrations.alipay.config import (
    get_alipay_config,
)
from backend.app.integrations.alipay.verifier import (
    verify_alipay_notification,
)
from backend.app.services.payment_service import (
    get_payment_by_id_for_update,
    mark_payment_success,
)
from backend.app.services.subscription_service import (
    activate_subscription,
)


class AlipayCallbackError(Exception):
    """Base Alipay callback error."""


def process_alipay_callback(
    database: Session,
    *,
    data: dict[str, str],
):
    """
    Verify and process an Alipay asynchronous
    payment notification.
    """

    # Signature verification must happen first.
    verify_alipay_notification(
        data,
    )

    payment_id_raw = data.get(
        "out_trade_no",
    )
    trade_no = data.get(
        "trade_no",
    )
    trade_status = data.get(
        "trade_status",
    )
    total_amount_raw = data.get(
        "total_amount",
    )
    callback_app_id = data.get(
        "app_id",
    )

    if (
        not payment_id_raw
        or not trade_no
        or not trade_status
        or not total_amount_raw
        or not callback_app_id
    ):
        raise AlipayCallbackError(
            "Missing required Alipay callback fields."
        )

    # Verify that the callback belongs to our
    # configured Alipay application.
    config = get_alipay_config()

    if (
        not config.app_id
        or callback_app_id != config.app_id
    ):
        raise AlipayCallbackError(
            "Invalid Alipay app ID."
        )

    # Only successful Alipay transaction states
    # may activate a subscription.
    if trade_status not in {
        "TRADE_SUCCESS",
        "TRADE_FINISHED",
    }:
        raise AlipayCallbackError(
            "Alipay trade is not successful."
        )

    # Convert our merchant order ID safely.
    try:
        payment_id = uuid.UUID(
            payment_id_raw,
        )
    except (
        ValueError,
        TypeError,
        AttributeError,
    ) as error:
        raise AlipayCallbackError(
            "Invalid Alipay merchant order ID."
        ) from error

    payment = get_payment_by_id_for_update(
        database,
        payment_id=payment_id,
    )

    # A callback must never complete a transaction
    # created for another payment provider.
    if payment.provider != "alipay":
        raise AlipayCallbackError(
            "Payment provider mismatch."
        )

    # Database amounts are stored in minor units.
    # Example: 100 CNY cents == 1.00 CNY.
    expected_amount = (
        Decimal(payment.amount)
        / Decimal("100")
    )

    try:
        callback_amount = Decimal(
            total_amount_raw,
        )
    except (
        InvalidOperation,
        ValueError,
    ) as error:
        raise AlipayCallbackError(
            "Invalid Alipay payment amount."
        ) from error

    if callback_amount != expected_amount:
        raise AlipayCallbackError(
            "Alipay payment amount mismatch."
        )

    # Idempotent replay:
    # the same completed payment + same Alipay trade
    # may safely return success.
    if payment.status == "success":
        if (
            payment.provider_transaction_id
            != trade_no
        ):
            raise AlipayCallbackError(
                "Alipay transaction ID mismatch."
            )

        return payment

    if payment.status != "pending":
        raise AlipayCallbackError(
            "Payment is not pending."
        )

    payment = mark_payment_success(
        database,
        user_id=payment.user_id,
        payment_id=payment.id,
        provider_transaction_id=trade_no,
        commit=False,
    )

    activate_subscription(
        database,
        user_id=payment.user_id,
        plan_id=payment.subscription_plan_id,
        commit=False,
    )

    database.commit()
    database.refresh(payment)

    return payment