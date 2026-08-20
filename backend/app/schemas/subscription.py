import uuid

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