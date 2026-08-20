"""add user subscriptions

Revision ID: 0a0ff2d37660
Revises: 98d20ecbc8f3
Create Date: 2026-08-21 03:15:05.542591

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0a0ff2d37660"
down_revision: Union[str, Sequence[str], None] = "98d20ecbc8f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create user subscriptions table."""

    op.create_table(
        "user_subscriptions",
        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "plan_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="active",
            nullable=False,
        ),
        sa.Column(
            "price_minor_units",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "currency",
            sa.String(length=3),
            nullable=False,
        ),
        sa.Column(
            "duration_days",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "data_limit_bytes",
            sa.BigInteger(),
            nullable=True,
        ),
        sa.Column(
            "max_devices",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "starts_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "ends_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "cancelled_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('active', 'expired', 'cancelled')",
            name="ck_user_subscriptions_status_valid",
        ),
        sa.CheckConstraint(
            "data_limit_bytes IS NULL OR data_limit_bytes > 0",
            name="ck_user_subscriptions_data_limit_positive",
        ),
        sa.CheckConstraint(
            "duration_days > 0",
            name="ck_user_subscriptions_duration_positive",
        ),
        sa.CheckConstraint(
            "ends_at > starts_at",
            name="ck_user_subscriptions_period_valid",
        ),
        sa.CheckConstraint(
            "max_devices > 0",
            name="ck_user_subscriptions_devices_positive",
        ),
        sa.CheckConstraint(
            "price_minor_units >= 0",
            name="ck_user_subscriptions_price_nonnegative",
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["subscription_plans.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_user_subscriptions_plan_id"),
        "user_subscriptions",
        ["plan_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_user_subscriptions_user_id"),
        "user_subscriptions",
        ["user_id"],
        unique=False,
    )

    op.create_index(
        "ix_user_subscriptions_user_status",
        "user_subscriptions",
        ["user_id", "status"],
        unique=False,
    )

    op.create_index(
        "uq_user_subscriptions_one_active_per_user",
        "user_subscriptions",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )


def downgrade() -> None:
    """Remove user subscriptions table."""

    op.drop_index(
        "uq_user_subscriptions_one_active_per_user",
        table_name="user_subscriptions",
    )

    op.drop_index(
        "ix_user_subscriptions_user_status",
        table_name="user_subscriptions",
    )

    op.drop_index(
        op.f("ix_user_subscriptions_user_id"),
        table_name="user_subscriptions",
    )

    op.drop_index(
        op.f("ix_user_subscriptions_plan_id"),
        table_name="user_subscriptions",
    )

    op.drop_table("user_subscriptions")