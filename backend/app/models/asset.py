from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Asset(Base):
    __tablename__ = "assets"
    __table_args__ = (
        Index("idx_asset_user_month", "user_id", "snapshot_month"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    snapshot_month: Mapped[str] = mapped_column(String(7))
    asset_type: Mapped[str] = mapped_column(String(16))      # cash/deposit/stock/fund/other
    account_name: Mapped[str] = mapped_column(String(64))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    remark: Mapped[str | None] = mapped_column(String(255))


class AssetItem(Base):
    __tablename__ = "asset_items"
    __table_args__ = (UniqueConstraint("user_id", "kind", "name", name="uq_asset_item_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(64))
    kind: Mapped[str] = mapped_column(String(16))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    legacy_type: Mapped[str | None] = mapped_column(String(16))


class AssetMonthValue(Base):
    __tablename__ = "asset_month_values"
    __table_args__ = (UniqueConstraint("item_id", "month", name="uq_asset_item_month"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("asset_items.id", ondelete="CASCADE"), index=True)
    month: Mapped[str] = mapped_column(String(7))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    remark: Mapped[str | None] = mapped_column(String(255))
