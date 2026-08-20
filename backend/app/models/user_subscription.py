import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class UserSubscription(Base):
    __tablename__ = "user_subscriptions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'expired', 'cancelled')",
            name="ck_user_subscriptions_status_valid",
        ),
        CheckConstraint(
            "ends_at > starts_at",
            name="ck_user_subscriptions_period_valid",
        ),
        CheckConstraint(
            "price_minor_units >= 0",
            name="ck_user_subscriptions_price_nonnegative",
        ),
        CheckConstraint(
            "duration_days > 0",
            name="ck_user_subscriptions_duration_positive",
        ),
        CheckConstraint(
            "max_devices > 0",
            name="ck_user_subscriptions_devices_positive",
        ),
        CheckConstraint(
            "data_limit_bytes IS NULL OR data_limit_bytes > 0",
            name="ck_user_subscriptions_data_limit_positive",
        ),
       Index(
            "ix_user_subscriptions_user_status",
            "user_id",
            "status",
        ),
        Index(
            "uq_user_subscriptions_one_active_per_user",
            "user_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "subscription_plans.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        server_default="active",
    )
    price_minor_units: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )
    duration_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    data_limit_bytes: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )
    max_devices: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    ends_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )