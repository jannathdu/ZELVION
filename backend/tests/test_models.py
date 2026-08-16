from sqlalchemy import inspect

from backend.app.db.session import engine


def test_expected_tables_exist() -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    assert {
    "users",
    "roles",
    "user_roles",
    "refresh_sessions",
}.issubset(table_names)


def test_user_roles_constraints() -> None:
    inspector = inspect(engine)

    primary_key = inspector.get_pk_constraint("user_roles")
    assert set(primary_key["constrained_columns"]) == {"user_id", "role_id"}

    foreign_keys = inspector.get_foreign_keys("user_roles")
    referenced_tables = {key["referred_table"] for key in foreign_keys}

    assert referenced_tables == {"users", "roles"}
    assert all(
        key["options"].get("ondelete") == "CASCADE"
        for key in foreign_keys
    )

def test_refresh_session_constraints() -> None:
    inspector = inspect(engine)

    foreign_keys = inspector.get_foreign_keys("refresh_sessions")
    assert len(foreign_keys) == 1
    assert foreign_keys[0]["referred_table"] == "users"
    assert foreign_keys[0]["options"].get("ondelete") == "CASCADE"

    indexes = inspector.get_indexes("refresh_sessions")
    token_index = next(
        index
        for index in indexes
        if index["name"] == "ix_refresh_sessions_token_jti"
    )
    assert token_index["unique"] is True