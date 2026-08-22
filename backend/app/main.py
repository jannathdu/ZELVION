import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.v1.router import api_router
from backend.app.core.config import Settings, get_settings


logger = logging.getLogger("zelvion.api")


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

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """
        Log unexpected server errors internally while
        returning only a generic response to the client.
        """

        logger.error(
            "Unhandled exception during %s %s",
            request.method,
            request.url.path,
            exc_info=(
                type(exc),
                exc,
                exc.__traceback__,
            ),
        )

        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
            },
        )

    app.include_router(
        api_router,
        prefix="/api/v1",
    )

    return app


app = create_app()