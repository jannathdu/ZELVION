from sqlalchemy import text

from backend.app.db.session import engine


def test_database_connection() -> None:
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT current_user, current_database()")
        ).one()

    assert result._mapping["current_user"] == "zelvion_app"
    assert result._mapping["current_database"] == "zelvion_dev"