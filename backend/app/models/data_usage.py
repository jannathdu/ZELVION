import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class DataUsage(Base):
    __tablename__ = "data_usage_records"
    __table_args__ = (
        CheckConstraint(
            "bytes_used > 0",
            name="ck_data_usage_bytes_positive",
        ),
        CheckConstraint(
            "record_type IN ('upload', 'download', 'total')",
            name="ck_data_usage_record_type_valid",
        ),
        Index(
            "ix_data_usage_user_created",
            "user_id",
            "created_at",
        ),
        Index(
            "ix_data_usage_subscription_created",
            "subscription_id",
            "created_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    subscription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "user_subscriptions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    bytes_used: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    record_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="total",
        server_default="total",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )