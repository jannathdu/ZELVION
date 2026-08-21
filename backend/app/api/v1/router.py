from fastapi import APIRouter

from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.devices import router as devices_router
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.subscriptions import (
    router as subscriptions_router,
)


api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(subscriptions_router)
api_router.include_router(devices_router)