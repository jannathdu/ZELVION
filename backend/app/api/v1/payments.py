import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import CurrentUser
from backend.app.db.session import get_db
from backend.app.schemas.payment import (
    PaymentCreateRequest,
    PaymentHistoryResponse,
    PaymentResponse,
    PaymentSuccessRequest,
)
from backend.app.services.payment_service import (
    InvalidPaymentStatusError,
    PlanNotFoundError,
    create_payment_order,
    get_payment_history,
    mark_payment_success,
)


router = APIRouter(
    prefix="/payments",
    tags=["payments"],
)

DatabaseSession = Annotated[Session, Depends(get_db)]

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
            subscription_plan_id=payload.subscription_plan_id,
            provider=payload.provider,
        )

    except PlanNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription plan not found",
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
    try:
        return mark_payment_success(
            database,
            payment_id=payment_id,
            provider_transaction_id=(
                payload.provider_transaction_id
            ),
        )

    except InvalidPaymentStatusError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Invalid payment status",
        ) from None

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        ) from None

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