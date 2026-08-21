import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DataUsageCreateRequest(BaseModel):
    bytes_used: int
    record_type: str = "total"


class DataUsageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    bytes_used: int
    record_type: str
    created_at: datetime


class DataUsageSummaryResponse(BaseModel):
    used_bytes: int
    limit_bytes: int | None
    remaining_bytes: int | None