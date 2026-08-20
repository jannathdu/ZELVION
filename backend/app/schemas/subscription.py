import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class SubscriptionPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    description: str | None
    price_minor_units: int
    currency: str
    duration_days: int
    data_limit_bytes: int | None
    max_devices: int


class UserSubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    plan_id: uuid.UUID
    status: Literal["active", "expired", "cancelled"]
    price_minor_units: int
    currency: str
    duration_days: int
    data_limit_bytes: int | None
    max_devices: int
    starts_at: datetime
    ends_at: datetime
    cancelled_at: datetime | None
    created_at: datetime
    updated_at: datetime