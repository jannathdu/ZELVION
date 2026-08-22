from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.v1.router import api_router
from backend.app.core.config import Settings, get_settings


def create_app(
    settings: Settings | None = None,
) -> FastAPI:
    app_settings = settings or get_settings()

    is_production = (
        app_settings.environment == "production"
    )

    app = FastAPI(
        title=app_settings.app_name,
        version=app_settings.app_version,
        docs_url=None if is_production else "/docs",
        redoc_url=None if is_production else "/redoc",
        openapi_url=(
            None
            if is_production
            else "/openapi.json"
        ),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            app_settings.frontend_origin,
        ],
        allow_credentials=False,
        allow_methods=[
            "GET",
            "POST",
            "DELETE",
        ],
        allow_headers=[
            "Authorization",
            "Content-Type",
        ],
    )

    app.include_router(
        api_router,
        prefix="/api/v1",
    )

    return app


app = create_app()