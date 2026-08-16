import uuid

from fastapi.testclient import TestClient
from sqlalchemy import delete

from backend.app.db.session import SessionLocal
from backend.app.main import app
from backend.app.models.user import User


client = TestClient(app)


def test_registration_login_and_refresh_flow() -> None:
    email = f"auth-test-{uuid.uuid4()}@example.com"
    password = "Strong-Test-Password-123!"

    try:
        registration_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
            },
        )

        assert registration_response.status_code == 201
        registration_data = registration_response.json()
        assert registration_data["email"] == email
        assert registration_data["is_active"] is True
        assert registration_data["is_verified"] is False
        assert "password" not in registration_data
        assert "password_hash" not in registration_data

        duplicate_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
            },
        )
        assert duplicate_response.status_code == 409

        wrong_password_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": "Wrong-Password",
            },
        )
        assert wrong_password_response.status_code == 401

        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": password,
            },
        )

        assert login_response.status_code == 200
        login_data = login_response.json()
        assert login_data["token_type"] == "bearer"
        assert login_data["access_token"]
        assert login_data["refresh_token"]
        assert login_data["expires_in"] == 900

        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={
                "refresh_token": login_data["refresh_token"],
            },
        )

        assert refresh_response.status_code == 200
        refresh_data = refresh_response.json()
        assert refresh_data["access_token"]
        assert refresh_data["refresh_token"]
        assert refresh_data["access_token"] != login_data["access_token"]

    finally:
        with SessionLocal() as database:
            database.execute(
                delete(User).where(User.email == email)
            )
            database.commit()