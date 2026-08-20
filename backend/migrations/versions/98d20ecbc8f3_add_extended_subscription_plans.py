"""add extended subscription plans

Revision ID: 98d20ecbc8f3
Revises: 2a8b9b0567da
Create Date: 2026-08-21 02:54:27.780219

"""

import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "98d20ecbc8f3"
down_revision: Union[str, Sequence[str], None] = "2a8b9b0567da"
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
    """Insert extended ZELVION development plans."""

    op.bulk_insert(
        plans_table,
        [
            {
                "id": uuid.UUID(
                    "ad934013-a207-45f8-8d72-08f278442b2a"
                ),
                "code": "three-month",
                "name": "3-Month Plan",
                "description": (
                    "Three months of secure access for up to "
                    "three devices."
                ),
                "price_minor_units": 3000,
                "currency": "CNY",
                "duration_days": 90,
                "data_limit_bytes": 670_014_898_176,
                "max_devices": 3,
                "is_active": True,
            },
            {
                "id": uuid.UUID(
                    "0dc75285-141d-446d-a6a4-55858b999762"
                ),
                "code": "six-month",
                "name": "6-Month Plan",
                "description": (
                    "Six months of secure access for up to "
                    "three devices."
                ),
                "price_minor_units": 6000,
                "currency": "CNY",
                "duration_days": 180,
                "data_limit_bytes": 1_340_029_796_352,
                "max_devices": 3,
                "is_active": True,
            },
            {
                "id": uuid.UUID(
                    "db33a879-f023-4d48-af46-b12043560745"
                ),
                "code": "twelve-month",
                "name": "12-Month Plan",
                "description": (
                    "Twelve months of secure access for up to "
                    "three devices."
                ),
                "price_minor_units": 10800,
                "currency": "CNY",
                "duration_days": 360,
                "data_limit_bytes": 2_680_059_592_704,
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
                [
                    "three-month",
                    "six-month",
                    "twelve-month",
                ]
            )
        )
    )