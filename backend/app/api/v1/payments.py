import uuid
from typing import Annotated
from urllib.parse import parse_qsl

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from backend.app.api.dependencies import CurrentUser
from backend.app.core.config import get_settings
from backend.app.db.session import get_db
from backend.app.schemas.payment import (
    AlipayOrderResponse,
    PaymentCreateRequest,
    PaymentHistoryResponse,
    PaymentResponse,
    PaymentSuccessRequest,
)
from backend.app.services.alipay_callback_service import (
    process_alipay_callback,
)
from backend.app.services.alipay_payment_service import (
    create_alipay_payment_url,
)
from backend.app.services.payment_service import (
    ActiveSubscriptionPaymentError,
    InvalidPaymentStatusError,
    PaymentNotFoundError,
    PlanNotFoundError,
    create_payment_order,
    get_payment_for_update,
    get_payment_history,
    mark_payment_success,
)
from backend.app.services.subscription_service import (
    ActiveSubscriptionExistsError,
    SubscriptionPlanUnavailableError,
    activate_subscription,
)


router = APIRouter(
    prefix="/payments",
    tags=["payments"],
)


DatabaseSession = Annotated[
    Session,
    Depends(get_db),
]


@router.post(
    "/create",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_payment(
    payload: PaymentCreateRequest,
    current_user: CurrentUser,
    database: DatabaseSession,
) -> PaymentResponse:
    try:
        return create_payment_order(
            database,
            user_id=current_user.id,
            subscription_plan_id=(
                payload.subscription_plan_id
            ),
            provider=payload.provider,
        )

    except ActiveSubscriptionPaymentError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "An active subscription already exists"
            ),
        ) from None

    except PlanNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription plan not found",
        ) from None


@router.post(
    "/{payment_id}/alipay-order",
    response_model=AlipayOrderResponse,
)
def create_alipay_order(
    payment_id: uuid.UUID,
    current_user: CurrentUser,
    database: DatabaseSession,
) -> AlipayOrderResponse:
    try:
        payment = get_payment_for_update(
            database,
            user_id=current_user.id,
            payment_id=payment_id,
        )

        if payment.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Payment is not pending",
            )

        payment_url = create_alipay_payment_url(
            payment,
        )

        database.commit()

        return AlipayOrderResponse(
            payment_id=payment.id,
            payment_url=payment_url,
        )

    except PaymentNotFoundError:
        database.rollback()

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        ) from None


@router.post(
    "/{payment_id}/success",
    response_model=PaymentResponse,
)
def payment_success(
    payment_id: uuid.UUID,
    payload: PaymentSuccessRequest,
    current_user: CurrentUser,
    database: DatabaseSession,
) -> PaymentResponse:
    settings = get_settings()

    if not settings.enable_mock_subscription_activation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        )

    try:
        existing_payment = get_payment_for_update(
            database,
            user_id=current_user.id,
            payment_id=payment_id,
        )

        if existing_payment.status == "success":
            if (
                existing_payment.provider_transaction_id
                == payload.provider_transaction_id
            ):
                database.commit()
                database.refresh(existing_payment)

                return existing_payment

            raise InvalidPaymentStatusError

        if existing_payment.status != "pending":
            raise InvalidPaymentStatusError

        payment = mark_payment_success(
            database,
            user_id=current_user.id,
            payment_id=payment_id,
            provider_transaction_id=(
                payload.provider_transaction_id
            ),
            commit=False,
        )

        activate_subscription(
            database,
            user_id=current_user.id,
            plan_id=payment.subscription_plan_id,
            commit=False,
        )

        database.commit()
        database.refresh(payment)

        return payment

    except PaymentNotFoundError:
        database.rollback()

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        ) from None

    except InvalidPaymentStatusError:
        database.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Invalid payment status",
        ) from None

    except SubscriptionPlanUnavailableError:
        database.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Subscription plan unavailable",
        ) from None

    except ActiveSubscriptionExistsError:
        database.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "An active subscription already exists"
            ),
        ) from None


@router.post(
    "/alipay/notify",
    response_class=PlainTextResponse,
)
async def alipay_notify(
    request: Request,
    database: DatabaseSession,
) -> PlainTextResponse:
    """
    Receive Alipay asynchronous payment notification.

    Alipay sends callback parameters as
    application/x-www-form-urlencoded data.
    """

    try:
        raw_body = await request.body()

        form_data = dict(
            parse_qsl(
                raw_body.decode("utf-8"),
                keep_blank_values=True,
            )
        )

        process_alipay_callback(
            database,
            data=form_data,
        )

        return PlainTextResponse(
            content="success",
            status_code=status.HTTP_200_OK,
        )

    except Exception:
        database.rollback()

        return PlainTextResponse(
            content="failure",
            status_code=status.HTTP_200_OK,
        )


@router.get(
    "/history",
    response_model=PaymentHistoryResponse,
)
def payment_history(
    current_user: CurrentUser,
    database: DatabaseSession,
) -> PaymentHistoryResponse:
    payments = get_payment_history(
        database,
        user_id=current_user.id,
    )

    return PaymentHistoryResponse(
        payments=payments,
    )