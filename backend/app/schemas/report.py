from decimal import Decimal

from pydantic import BaseModel


class MonthBucket(BaseModel):
    year_month: str
    income: Decimal = Decimal("0.00")
    expense: Decimal = Decimal("0.00")
    balance: Decimal = Decimal("0.00")


class YearlyReportOut(BaseModel):
    year: int
    buckets: list[MonthBucket]
    total_income: Decimal
    total_expense: Decimal
    total_balance: Decimal


class CategoryBucket(BaseModel):
    category_id: int | None
    category_name: str | None
    amount: Decimal
    count: int
    percent: float


class CategorySummaryOut(BaseModel):
    year_month: str
    total_expense: Decimal
    buckets: list[CategoryBucket]


class AssetBucket(BaseModel):
    asset_type: str
    amount: Decimal
    count: int


class BalanceOut(BaseModel):
    year_month: str
    asset_total: Decimal
    buckets: list[AssetBucket]


class MonthlyOverviewOut(BaseModel):
    year_month: str
    bill_expense: Decimal
    bill_income: Decimal
    declared_income: Decimal       # 来自 monthly_incomes
    asset_total: Decimal
    net_worth_change: Decimal      # asset_total - prev_month asset_total
