import uuid
from datetime import datetime

from pydantic import BaseModel


class DashboardUserResponse(BaseModel):
    id: uuid.UUID
    email: str


class DashboardSubscriptionResponse(BaseModel):
    plan_name: str | None
    status: str | None
    starts_at: datetime | None
    ends_at: datetime | None


class DashboardUsageResponse(BaseModel):
    used_bytes: int
    limit_bytes: int | None
    remaining_bytes: int | None


class DashboardDeviceResponse(BaseModel):
    total_devices: int
    max_devices: int | None


class DashboardPaymentResponse(BaseModel):
    last_payment_status: str | None
    last_payment_date: datetime | None


class DashboardResponse(BaseModel):
    user: DashboardUserResponse
    subscription: DashboardSubscriptionResponse
    usage: DashboardUsageResponse
    devices: DashboardDeviceResponse
    payments: DashboardPaymentResponse