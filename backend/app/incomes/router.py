from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import delete, select

from app.core.deps import CurrentUser, SessionDep
from app.core.response import ok
from app.models.income import IncomeEntry, MonthlyIncome
from app.schemas.finance import IncomeIn, IncomeOut, IncomePatchIn
from app.schemas.monthly_finance import IncomeEntryIn, IncomeEntryPatch

router = APIRouter(prefix="/incomes", tags=["incomes"])
entries_router = APIRouter(tags=["income-entries"])


def _bounds(year: int, month: int | None = None) -> tuple[datetime, datetime]:
    if month is None:
        return datetime(year, 1, 1), datetime(year + 1, 1, 1)
    start = datetime(year, month, 1)
    end = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)
    return start, end


def _entry_dict(entry: IncomeEntry) -> dict:
    return {"id": entry.id, "occurred_at": entry.occurred_at.isoformat(),
            "amount": str(entry.amount), "source": entry.source, "remark": entry.remark}


@entries_router.get("/income-entries")
async def list_income_entries(user: CurrentUser, session: SessionDep, month: str | None = None,
                              year: int | None = None) -> dict:
    q = select(IncomeEntry).where(IncomeEntry.user_id == user.id)
    if month:
        try:
            y, m = map(int, month.split("-"))
            start, end = _bounds(y, m)
        except (ValueError, TypeError) as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "invalid month") from exc
        q = q.where(IncomeEntry.occurred_at >= start, IncomeEntry.occurred_at < end)
    elif year:
        start, end = _bounds(year)
        q = q.where(IncomeEntry.occurred_at >= start, IncomeEntry.occurred_at < end)
    rows = list(await session.scalars(q.order_by(IncomeEntry.occurred_at.desc(), IncomeEntry.id.desc())))
    return ok([_entry_dict(r) for r in rows])


@entries_router.post("/income-entries")
async def create_income_entry(body: IncomeEntryIn, user: CurrentUser, session: SessionDep) -> dict:
    entry = IncomeEntry(user_id=user.id, **body.model_dump())
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return ok(_entry_dict(entry))


@entries_router.patch("/income-entries/{entry_id}")
async def patch_income_entry(entry_id: int, body: IncomeEntryPatch, user: CurrentUser, session: SessionDep) -> dict:
    entry = await session.scalar(select(IncomeEntry).where(IncomeEntry.id == entry_id, IncomeEntry.user_id == user.id))
    if not entry:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "income entry not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        if key in ("occurred_at", "amount") and value is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"{key} cannot be null")
        setattr(entry, key, value)
    await session.commit()
    await session.refresh(entry)
    return ok(_entry_dict(entry))


@entries_router.delete("/income-entries/{entry_id}")
async def delete_income_entry(entry_id: int, user: CurrentUser, session: SessionDep) -> dict:
    entry = await session.scalar(select(IncomeEntry).where(IncomeEntry.id == entry_id, IncomeEntry.user_id == user.id))
    if not entry:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "income entry not found")
    await session.delete(entry)
    await session.commit()
    return ok({"deleted": entry_id})


@entries_router.get("/income-summary")
async def income_summary(user: CurrentUser, session: SessionDep,
                         year: int = Query(..., ge=1900, le=9998), month: str | None = None) -> dict:
    month = month or f"{year}-01"
    try:
        y, m = map(int, month.split("-"))
        month_start, month_end = _bounds(y, m)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "invalid month") from exc
    if y != year:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "month and year differ")
    year_start, year_end = _bounds(year)
    entries = list(await session.scalars(
        select(IncomeEntry).where(IncomeEntry.user_id == user.id,
                                  IncomeEntry.occurred_at >= year_start,
                                  IncomeEntry.occurred_at < year_end)
    ))
    legacy = list(await session.scalars(
        select(MonthlyIncome).where(MonthlyIncome.user_id == user.id,
                                    MonthlyIncome.year_month.like(f"{year}-%"))
    ))
    monthly_entries = [e for e in entries if month_start <= e.occurred_at < month_end]
    monthly_legacy = [e for e in legacy if e.year_month == month]
    return ok({
        "year": year, "month": month,
        "month_total": str(sum((e.amount for e in monthly_entries), Decimal("0")) +
                           sum((e.amount for e in monthly_legacy), Decimal("0"))),
        "year_total": str(sum((e.amount for e in entries), Decimal("0")) +
                          sum((e.amount for e in legacy), Decimal("0"))),
        "legacy_monthly": [{"id": e.id, "year_month": e.year_month,
                            "source": e.source, "amount": str(e.amount), "remark": e.remark}
                           for e in monthly_legacy],
    })


@router.get("")
async def list_incomes(
    user: CurrentUser,
    session: SessionDep,
    year: str | None = Query(default=None, min_length=4, max_length=4),
    month: str | None = Query(default=None, min_length=7, max_length=7),
) -> dict:
    q = select(MonthlyIncome).where(MonthlyIncome.user_id == user.id)
    if month:
        q = q.where(MonthlyIncome.year_month == month)
    elif year:
        q = q.where(MonthlyIncome.year_month.like(f"{year}-%"))
    q = q.order_by(MonthlyIncome.year_month.desc(), MonthlyIncome.id)
    rows = (await session.scalars(q)).all()
    return ok([IncomeOut.model_validate(r).model_dump(mode="json") for r in rows])


@router.post("")
async def create_income(body: IncomeIn, user: CurrentUser, session: SessionDep) -> dict:
    dup = await session.scalar(
        select(MonthlyIncome).where(
            MonthlyIncome.user_id == user.id,
            MonthlyIncome.year_month == body.year_month,
            MonthlyIncome.source == body.source,
        )
    )
    if dup:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"income for {body.year_month}/{body.source} already exists",
        )
    inc = MonthlyIncome(user_id=user.id, **body.model_dump())
    session.add(inc)
    await session.commit()
    await session.refresh(inc)
    return ok(IncomeOut.model_validate(inc).model_dump(mode="json"))


@router.patch("/{income_id}")
async def patch_income(
    income_id: int, body: IncomePatchIn, user: CurrentUser, session: SessionDep
) -> dict:
    inc = await session.scalar(
        select(MonthlyIncome).where(
            MonthlyIncome.id == income_id, MonthlyIncome.user_id == user.id
        )
    )
    if not inc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "income not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(inc, k, v)
    await session.commit()
    await session.refresh(inc)
    return ok(IncomeOut.model_validate(inc).model_dump(mode="json"))


@router.delete("/{income_id}")
async def delete_income(income_id: int, user: CurrentUser, session: SessionDep) -> dict:
    inc = await session.scalar(
        select(MonthlyIncome).where(
            MonthlyIncome.id == income_id, MonthlyIncome.user_id == user.id
        )
    )
    if not inc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "income not found")
    await session.execute(delete(MonthlyIncome).where(MonthlyIncome.id == income_id))
    await session.commit()
    return ok({"deleted": income_id})
