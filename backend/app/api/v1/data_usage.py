import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import CurrentUser
from backend.app.db.session import get_db
from backend.app.schemas.data_usage import (
    DataUsageCreateRequest,
    DataUsageResponse,
    DataUsageSummaryResponse,
)
from backend.app.services.data_usage_service import (
    DataQuotaExceededError,
    NoActiveSubscriptionError,
    get_usage_summary,
    record_usage,
)


router = APIRouter(
    prefix="/usage",
    tags=["usage"],
)

DatabaseSession = Annotated[Session, Depends(get_db)]

@router.post(
    "",
    response_model=DataUsageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_usage_record(
    payload: DataUsageCreateRequest,
    current_user: CurrentUser,
    database: DatabaseSession,
) -> DataUsageResponse:
    try:
        return record_usage(
            database,
            user_id=current_user.id,
            bytes_used=payload.bytes_used,
            record_type=payload.record_type,
        )

    except NoActiveSubscriptionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active subscription required",
        ) from None

    except DataQuotaExceededError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Data quota exceeded",
        ) from None

@router.get(
    "/summary",
    response_model=DataUsageSummaryResponse,
)
def get_my_usage_summary(
    current_user: CurrentUser,
    database: DatabaseSession,
) -> DataUsageSummaryResponse:
    try:
        return get_usage_summary(
            database,
            user_id=current_user.id,
        )

    except NoActiveSubscriptionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active subscription required",
        ) from None