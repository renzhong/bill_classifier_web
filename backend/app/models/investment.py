from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class InvestmentItem(Base):
    __tablename__ = "investment_items"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_investment_name"),
        UniqueConstraint("linked_asset_item_id", name="uq_investment_linked_asset"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(64))
    initial_principal: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    first_month: Mapped[str] = mapped_column(String(7))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    linked_asset_item_id: Mapped[int | None] = mapped_column(ForeignKey("asset_items.id"))


class InvestmentMonth(Base):
    __tablename__ = "investment_months"
    __table_args__ = (UniqueConstraint("item_id", "month", name="uq_investment_month"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("investment_items.id", ondelete="CASCADE"), index=True)
    month: Mapped[str] = mapped_column(String(7))
    buys: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    sells: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    closing_value: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
