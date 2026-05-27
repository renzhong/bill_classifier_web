from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class MonthlyIncome(Base):
    __tablename__ = "monthly_incomes"
    __table_args__ = (
        UniqueConstraint("user_id", "year_month", "source", name="uq_income_user_month_source"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    year_month: Mapped[str] = mapped_column(String(7))    # YYYY-MM
    source: Mapped[str] = mapped_column(String(64))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    remark: Mapped[str | None] = mapped_column(String(255))
