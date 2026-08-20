from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.subscription_plan import SubscriptionPlan
from backend.app.schemas.subscription import (
    SubscriptionPlanResponse,
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