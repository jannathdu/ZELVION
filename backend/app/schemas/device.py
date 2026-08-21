import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DeviceCreateRequest(BaseModel):
    device_key_hash: str
    name: str
    platform: str


class DeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    device_key_hash: str
    name: str
    platform: str
    is_active: bool
    last_seen_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime
    updated_at: datetime