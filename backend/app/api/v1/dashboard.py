from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.api.dependencies import CurrentUser
from backend.app.db.session import get_db
from backend.app.schemas.dashboard import DashboardResponse
from backend.app.services.dashboard_service import (
    get_dashboard_data,
)


router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
)

DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get(
    "",
    response_model=DashboardResponse,
)
def get_my_dashboard(
    current_user: CurrentUser,
    database: DatabaseSession,
) -> DashboardResponse:
    return get_dashboard_data(
        database,
        user_id=current_user.id,
    )