from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.dependencies import CurrentUser
from backend.app.db.session import get_db
from backend.app.models.subscription_plan import SubscriptionPlan
from backend.app.models.user_subscription import UserSubscription
from backend.app.schemas.subscription import (
    SubscriptionPlanResponse,
    UserSubscriptionResponse,
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