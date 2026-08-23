import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PaymentCreateRequest(BaseModel):
    subscription_plan_id: uuid.UUID
    provider: str


class PaymentSuccessRequest(BaseModel):
    provider_transaction_id: str


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    subscription_plan_id: uuid.UUID
    amount: int
    currency: str
    provider: str
    provider_transaction_id: str | None
    status: str
    created_at: datetime
    paid_at: datetime | None


class PaymentHistoryResponse(BaseModel):
    payments: list[PaymentResponse]


class AlipayOrderResponse(BaseModel):
    payment_id: uuid.UUID
    payment_url: str

class AlipayNotifyRequest(BaseModel):
    out_trade_no: str
    trade_no: str
    trade_status: str
    total_amount: str
    sign: str