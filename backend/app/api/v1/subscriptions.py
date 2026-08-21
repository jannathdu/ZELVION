from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.dependencies import CurrentUser
from backend.app.core.config import get_settings
from backend.app.db.session import get_db
from backend.app.models.subscription_plan import SubscriptionPlan
from backend.app.models.user_subscription import UserSubscription
from backend.app.schemas.subscription import (
    SubscriptionActivationRequest,
    SubscriptionPlanResponse,
    UserSubscriptionResponse,
)
from backend.app.services.subscription_service import (
    ActiveSubscriptionExistsError,
    NoActiveSubscriptionError,
    SubscriptionPlanUnavailableError,
    activate_subscription,
    renew_subscription,
)

router = APIRouter(
    prefix="/subscriptions",
    tags=["subscriptions"],
)

DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get(
    "/plans",
    response_model=list[SubscriptionPlanResponse],
)
def list_subscription_plans(
    database: DatabaseSession,
) -> list[SubscriptionPlanResponse]:
    statement = (
        select(SubscriptionPlan)
        .where(SubscriptionPlan.is_active.is_(True))
        .order_by(
            SubscriptionPlan.price_minor_units,
            SubscriptionPlan.name,
        )
    )

    return list(database.scalars(statement).all())


@router.get(
    "/me",
    response_model=UserSubscriptionResponse | None,
)
def get_my_subscription(
    current_user: CurrentUser,
    database: DatabaseSession,
) -> UserSubscription | None:
    now = datetime.now(timezone.utc)

    statement = (
        select(UserSubscription)
        .where(
            UserSubscription.user_id == current_user.id,
            UserSubscription.status == "active",
            UserSubscription.ends_at > now,
        )
        .order_by(UserSubscription.ends_at.desc())
    )

    return database.scalars(statement).first()

@router.post(
    "/mock-activate",
    response_model=UserSubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
def mock_activate_subscription(
    payload: SubscriptionActivationRequest,
    current_user: CurrentUser,
    database: DatabaseSession,
) -> UserSubscription:
    settings = get_settings()

    if not settings.enable_mock_subscription_activation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        )

    try:
        return activate_subscription(
            database,
            user_id=current_user.id,
            plan_id=payload.plan_id,
        )
    except SubscriptionPlanUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription plan unavailable",
        ) from None
    except ActiveSubscriptionExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active subscription already exists",
        ) from None

@router.post(
    "/mock-renew",
    response_model=UserSubscriptionResponse,
)
def mock_renew_subscription(
    current_user: CurrentUser,
    database: DatabaseSession,
) -> UserSubscription:
    settings = get_settings()

    if not settings.enable_mock_subscription_activation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        )

    try:
        return renew_subscription(
            database,
            user_id=current_user.id,
        )
    except NoActiveSubscriptionError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No active subscription to renew",
        ) from None