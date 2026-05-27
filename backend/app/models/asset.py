from decimal import Decimal

from sqlalchemy import ForeignKey, Index, Numeric, String
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
