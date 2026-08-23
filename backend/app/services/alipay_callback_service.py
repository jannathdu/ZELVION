from sqlalchemy.orm import Session

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
    Process verified Alipay notification.
    """

    verify_alipay_notification(
        data,
    )

    payment_id = data.get(
        "out_trade_no",
    )

    trade_no = data.get(
        "trade_no",
    )

    if not payment_id or not trade_no:
        raise AlipayCallbackError(
            "Missing required Alipay callback fields."
        )

    payment = get_payment_by_id_for_update(
        database,
        payment_id=payment_id,
    )

    if payment.status == "success":
        return payment

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