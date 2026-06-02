from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Computed,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class UploadTask(Base):
    __tablename__ = "upload_tasks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    source: Mapped[str] = mapped_column(String(16))            # alipay/wechat
    filename: Mapped[str] = mapped_column(String(255))
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    classified_rows: Mapped[int] = mapped_column(Integer, default=0)
    error_msg: Mapped[str | None] = mapped_column(String(1024))

    tag_ids: Mapped[list[int]] = mapped_column(JSON, default=list)
    owner_label: Mapped[str | None] = mapped_column(String(32))

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)


class Bill(Base):
    __tablename__ = "bills"
    __table_args__ = (
        UniqueConstraint("user_id", "source", "order_id", name="uk_user_order"),
        Index("idx_user_time", "user_id", "bill_time"),
        Index("idx_user_month", "user_id", "bill_month"),
        Index("idx_user_cat", "user_id", "category_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    upload_task_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("upload_tasks.id"))

    source: Mapped[str] = mapped_column(String(16))
    owner: Mapped[str | None] = mapped_column(String(32))
    order_id: Mapped[str | None] = mapped_column(String(128))
    payee: Mapped[str | None] = mapped_column(String(255))
    item_name: Mapped[str | None] = mapped_column(String(512))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    bill_type: Mapped[str] = mapped_column(String(16), default="expense")
    bill_time: Mapped[datetime] = mapped_column(DateTime)
    # MySQL 生成列：CHAR(7) 'YYYY-MM'
    bill_month: Mapped[str] = mapped_column(
        String(7),
        Computed("DATE_FORMAT(bill_time, '%Y-%m')", persisted=True),
    )

    category_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("categories.id"))
    classify_strategy_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("pipeline_steps.id"))
    classify_strategy_type: Mapped[str | None] = mapped_column(String(64))

    lifecycle: Mapped[str] = mapped_column(String(32), default="unprocessed")
    skip_reason: Mapped[str | None] = mapped_column(String(64))
    group_id: Mapped[str | None] = mapped_column(String(64))
    is_merged: Mapped[bool] = mapped_column(Boolean, default=False)
    merged_from: Mapped[dict | None] = mapped_column(JSON)
    ai_provider: Mapped[str | None] = mapped_column(String(32))
    ai_confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))
    manual_overridden: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class BillTag(Base):
    __tablename__ = "bill_tags"

    bill_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("bills.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True, index=True
    )
