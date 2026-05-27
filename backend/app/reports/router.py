"""报表聚合端点：从 bills + monthly_incomes + assets 三个表算"""
from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Query
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, SessionDep
from app.core.response import ok
from app.models.asset import Asset
from app.models.bill import Bill
from app.models.category import Category
from app.models.income import MonthlyIncome
from app.schemas.report import (
    AssetBucket,
    BalanceOut,
    CategoryBucket,
    CategorySummaryOut,
    MonthBucket,
    MonthlyOverviewOut,
    YearlyReportOut,
)

router = APIRouter(prefix="/reports", tags=["reports"])

_SKIP_LIFECYCLE = ("skipped", "cross_month_refund")


def _to_d(x) -> Decimal:
    return Decimal(str(x or "0")).quantize(Decimal("0.01"))


async def _bills_sum_by_type(
    session: AsyncSession, user_id: int, *, month: str | None = None, year: str | None = None
) -> dict[str, Decimal]:
    """返回 {'income': sum, 'expense': sum, 'other': sum} （已剔除 skipped）"""
    q = (
        select(Bill.bill_type, func.coalesce(func.sum(Bill.amount), 0))
        .where(Bill.user_id == user_id, Bill.lifecycle.notin_(_SKIP_LIFECYCLE))
        .group_by(Bill.bill_type)
    )
    if month:
        q = q.where(Bill.bill_month == month)
    elif year:
        q = q.where(Bill.bill_month.like(f"{year}-%"))
    rows = await session.execute(q)
    out = {"income": Decimal("0.00"), "expense": Decimal("0.00"), "other": Decimal("0.00")}
    for bt, total in rows:
        out[bt] = _to_d(total)
    return out


async def _assets_total(session: AsyncSession, user_id: int, month: str) -> Decimal:
    total = await session.scalar(
        select(func.coalesce(func.sum(Asset.amount), 0)).where(
            Asset.user_id == user_id, Asset.snapshot_month == month
        )
    )
    return _to_d(total)


@router.get("/yearly")
async def yearly_report(
    user: CurrentUser, session: SessionDep, year: int = Query(...)
) -> dict:
    rows = await session.execute(
        select(
            Bill.bill_month,
            func.coalesce(
                func.sum(case((Bill.bill_type == "income", Bill.amount), else_=0)), 0
            ).label("income"),
            func.coalesce(
                func.sum(case((Bill.bill_type == "expense", Bill.amount), else_=0)), 0
            ).label("expense"),
        )
        .where(
            Bill.user_id == user.id,
            Bill.lifecycle.notin_(_SKIP_LIFECYCLE),
            Bill.bill_month.like(f"{year}-%"),
        )
        .group_by(Bill.bill_month)
        .order_by(Bill.bill_month)
    )
    by_month = {ym: (_to_d(inc), _to_d(exp)) for ym, inc, exp in rows}

    buckets = []
    total_income = Decimal("0.00")
    total_expense = Decimal("0.00")
    for m in range(1, 13):
        ym = f"{year}-{m:02d}"
        inc, exp = by_month.get(ym, (Decimal("0.00"), Decimal("0.00")))
        total_income += inc
        total_expense += exp
        buckets.append(MonthBucket(year_month=ym, income=inc, expense=exp, balance=inc - exp))

    return ok(
        YearlyReportOut(
            year=year,
            buckets=buckets,
            total_income=total_income,
            total_expense=total_expense,
            total_balance=total_income - total_expense,
        ).model_dump(mode="json")
    )


@router.get("/monthly")
async def monthly_overview(
    user: CurrentUser, session: SessionDep, month: str = Query(..., min_length=7, max_length=7)
) -> dict:
    sums = await _bills_sum_by_type(session, user.id, month=month)
    declared_income = await session.scalar(
        select(func.coalesce(func.sum(MonthlyIncome.amount), 0)).where(
            MonthlyIncome.user_id == user.id, MonthlyIncome.year_month == month
        )
    )
    asset_now = await _assets_total(session, user.id, month)

    # prev month
    year, mon = month.split("-")
    p_y, p_m = (int(year), int(mon) - 1) if int(mon) > 1 else (int(year) - 1, 12)
    prev_month = f"{p_y:04d}-{p_m:02d}"
    asset_prev = await _assets_total(session, user.id, prev_month)

    return ok(
        MonthlyOverviewOut(
            year_month=month,
            bill_expense=sums["expense"],
            bill_income=sums["income"],
            declared_income=_to_d(declared_income),
            asset_total=asset_now,
            net_worth_change=asset_now - asset_prev,
        ).model_dump(mode="json")
    )


@router.get("/category-summary")
async def category_summary(
    user: CurrentUser, session: SessionDep, month: str = Query(..., min_length=7, max_length=7)
) -> dict:
    rows = await session.execute(
        select(
            Bill.category_id,
            Category.name,
            func.coalesce(func.sum(Bill.amount), 0).label("amount"),
            func.count(Bill.id).label("cnt"),
        )
        .join(Category, Category.id == Bill.category_id, isouter=True)
        .where(
            Bill.user_id == user.id,
            Bill.lifecycle.notin_(_SKIP_LIFECYCLE),
            Bill.bill_month == month,
            Bill.bill_type == "expense",
        )
        .group_by(Bill.category_id, Category.name)
        .order_by(func.sum(Bill.amount).desc())
    )

    rows_list = list(rows)
    total = sum((_to_d(r[2]) for r in rows_list), Decimal("0.00"))
    buckets: list[CategoryBucket] = []
    for cat_id, name, amount, cnt in rows_list:
        a = _to_d(amount)
        pct = float(a / total * 100) if total > 0 else 0.0
        buckets.append(
            CategoryBucket(
                category_id=cat_id,
                category_name=name or "(未分类)",
                amount=a,
                count=int(cnt),
                percent=round(pct, 2),
            )
        )

    return ok(
        CategorySummaryOut(year_month=month, total_expense=total, buckets=buckets).model_dump(mode="json")
    )


@router.get("/balance")
async def balance_report(
    user: CurrentUser, session: SessionDep, month: str = Query(..., min_length=7, max_length=7)
) -> dict:
    rows = await session.execute(
        select(
            Asset.asset_type,
            func.coalesce(func.sum(Asset.amount), 0),
            func.count(Asset.id),
        )
        .where(Asset.user_id == user.id, Asset.snapshot_month == month)
        .group_by(Asset.asset_type)
        .order_by(Asset.asset_type)
    )
    buckets: list[AssetBucket] = []
    total = Decimal("0.00")
    for atype, amount, cnt in rows:
        a = _to_d(amount)
        total += a
        buckets.append(AssetBucket(asset_type=atype, amount=a, count=int(cnt)))

    return ok(BalanceOut(year_month=month, asset_total=total, buckets=buckets).model_dump(mode="json"))
