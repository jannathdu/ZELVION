from fastapi.testclient import TestClient

from backend.app.core.config import Settings
from backend.app.main import app, create_app


client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "zelvion-api",
    }

def test_configured_frontend_origin_is_allowed() -> None:
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert (
        response.headers["access-control-allow-origin"]
        == "http://localhost:5173"
    )


def test_unknown_frontend_origin_is_rejected() -> None:
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "https://malicious.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers

def test_production_disables_api_documentation() -> None:
    production_settings = Settings(
        environment="production",
        frontend_origin="https://app.zelvion.com",
        db_host="localhost",
        db_port=5432,
        db_name="zelvion_test",
        db_user="zelvion",
        db_password="test-database-password",
        jwt_secret_key=(
            "this-is-a-secure-production-test-secret-123456"
        ),
        enable_mock_subscription_activation=False,
        _env_file=None,
    )

    production_app = create_app(
        production_settings,
    )

    production_client = TestClient(
        production_app,
    )

    assert (
        production_client.get("/docs").status_code
        == 404
    )

    assert (
        production_client.get("/redoc").status_code
        == 404
    )

    assert (
        production_client.get(
            "/openapi.json",
        ).status_code
        == 404
    )

    health_response = production_client.get(
        "/api/v1/health",
    )

    assert health_response.status_code == 200

def test_unhandled_error_returns_generic_response() -> None:
    test_settings = Settings(
        environment="development",
        frontend_origin="http://localhost:5173",
        db_host="localhost",
        db_port=5432,
        db_name="zelvion_test",
        db_user="zelvion",
        db_password="test-database-password",
        jwt_secret_key=(
            "this-is-a-secure-development-test-secret-123456"
        ),
        enable_mock_subscription_activation=False,
        _env_file=None,
    )

    test_app = create_app(
        test_settings,
    )

    @test_app.get("/test-error")
    def test_error() -> None:
        raise RuntimeError(
            "sensitive internal test error"
        )

    test_client = TestClient(
        test_app,
        raise_server_exceptions=False,
    )

    response = test_client.get(
        "/test-error",
    )

    assert response.status_code == 500

    assert response.json() == {
        "detail": "Internal server error",
    }

    assert (
        "sensitive internal test error"
        not in response.text
    )