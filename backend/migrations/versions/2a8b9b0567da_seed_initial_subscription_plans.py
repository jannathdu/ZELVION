"""seed initial subscription plans

Revision ID: 2a8b9b0567da
Revises: 1606169dacb5
Create Date: 2026-08-21

"""

import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2a8b9b0567da"
down_revision: Union[str, Sequence[str], None] = "1606169dacb5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


plans_table = sa.table(
    "subscription_plans",
    sa.column("id", sa.UUID()),
    sa.column("code", sa.String()),
    sa.column("name", sa.String()),
    sa.column("description", sa.String()),
    sa.column("price_minor_units", sa.Integer()),
    sa.column("currency", sa.String()),
    sa.column("duration_days", sa.Integer()),
    sa.column("data_limit_bytes", sa.BigInteger()),
    sa.column("max_devices", sa.Integer()),
    sa.column("is_active", sa.Boolean()),
)


def upgrade() -> None:
    """Insert the initial ZELVION development plans."""

    op.bulk_insert(
        plans_table,
        [
            {
                "id": uuid.UUID(
                    "4d8b1e86-4fa1-4fbb-9077-32b9147f88a1"
                ),
                "code": "day-pass",
                "name": "1-Day Pass",
                "description": (
                    "Short-term secure access for one device."
                ),
                "price_minor_units": 100,
                "currency": "CNY",
                "duration_days": 1,
                "data_limit_bytes": 10_737_418_240,
                "max_devices": 1,
                "is_active": True,
            },
            {
                "id": uuid.UUID(
                    "a58db8c2-108e-4574-903d-a5725ee82790"
                ),
                "code": "monthly",
                "name": "Monthly Plan",
                "description": (
                    "Thirty days of secure access for up to "
                    "three devices."
                ),
                "price_minor_units": 1200,
                "currency": "CNY",
                "duration_days": 30,
                "data_limit_bytes": 223_338_299_392,
                "max_devices": 3,
                "is_active": True,
            },
        ],
    )


def downgrade() -> None:
    """Remove only the plans created by this migration."""

    op.execute(
        sa.delete(plans_table).where(
            plans_table.c.code.in_(
                ["day-pass", "monthly"]
            )
        )
    )