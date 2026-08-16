from fastapi import FastAPI


app = FastAPI(
    title="ZELVION API",
    version="0.1.0",
)


@app.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "zelvion-api",
    }