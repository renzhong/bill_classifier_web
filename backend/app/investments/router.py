from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.deps import CurrentUser, SessionDep
from app.core.response import ok
from app.models.asset import AssetItem
from app.models.investment import InvestmentItem, InvestmentMonth
from app.schemas.monthly_finance import InvestmentItemIn, InvestmentItemPatch, InvestmentMonthIn

router = APIRouter(tags=["investments"])


def _item_dict(item: InvestmentItem) -> dict:
    return {"id": item.id, "name": item.name, "initial_principal": str(item.initial_principal),
            "first_month": item.first_month, "active": item.active,
            "linked_asset_item_id": item.linked_asset_item_id}


async def _check_link(session: SessionDep, user_id: int, asset_id: int | None) -> None:
    if asset_id is None:
        return
    asset = await session.scalar(select(AssetItem).where(AssetItem.id == asset_id,
                                                        AssetItem.user_id == user_id,
                                                        AssetItem.kind == "asset"))
    if asset is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "linked asset item not found")


def _previous_month(month: str) -> str:
    year, number = map(int, month.split("-"))
    return f"{year - 1:04d}-12" if number == 1 else f"{year:04d}-{number - 1:02d}"


async def investment_month_rows(session, user_id: int, month: str) -> list[dict]:
    items = list(await session.scalars(
        select(InvestmentItem).where(InvestmentItem.user_id == user_id, InvestmentItem.first_month <= month)
        .order_by(InvestmentItem.id)
    ))
    if not items:
        return []
    ids = [i.id for i in items]
    periods = list(await session.scalars(
        select(InvestmentMonth).where(InvestmentMonth.item_id.in_(ids),
                                      InvestmentMonth.month.in_([month, _previous_month(month)]))
    ))
    values = {(p.item_id, p.month): p for p in periods}
    rows = []
    for item in items:
        current = values.get((item.id, month))
        if not item.active and current is None:
            continue
        previous = values.get((item.id, _previous_month(month)))
        base = item.initial_principal if month == item.first_month else (
            previous.closing_value if previous else None
        )
        closing = current.closing_value if current else None
        buys = current.buys if current else Decimal("0")
        sells = current.sells if current else Decimal("0")
        profit = closing - base - buys + sells if closing is not None and base is not None else None
        rows.append({**_item_dict(item), "month": month, "buys": str(buys), "sells": str(sells),
                     "closing_value": str(closing) if closing is not None else None,
                     "profit": str(profit) if profit is not None else None,
                     "missing_previous": closing is not None and base is None})
    return rows


@router.get("/investments")
async def list_investments(user: CurrentUser, session: SessionDep) -> dict:
    items = list(await session.scalars(
        select(InvestmentItem).where(InvestmentItem.user_id == user.id).order_by(InvestmentItem.id)
    ))
    return ok([_item_dict(i) for i in items])


@router.post("/investments")
async def create_investment(body: InvestmentItemIn, user: CurrentUser, session: SessionDep) -> dict:
    await _check_link(session, user.id, body.linked_asset_item_id)
    item = InvestmentItem(user_id=user.id, **body.model_dump())
    session.add(item)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "investment name already exists") from exc
    await session.refresh(item)
    return ok(_item_dict(item))


@router.patch("/investments/{item_id}")
async def patch_investment(item_id: int, body: InvestmentItemPatch, user: CurrentUser, session: SessionDep) -> dict:
    item = await session.scalar(select(InvestmentItem).where(InvestmentItem.id == item_id, InvestmentItem.user_id == user.id))
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "investment not found")
    if "linked_asset_item_id" in body.model_fields_set:
        await _check_link(session, user.id, body.linked_asset_item_id)
        item.linked_asset_item_id = body.linked_asset_item_id
    for key, value in body.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(item, key, value)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "investment name already exists") from exc
    await session.refresh(item)
    return ok(_item_dict(item))


@router.get("/investments/months/{month}")
async def get_investment_month(month: str, user: CurrentUser, session: SessionDep) -> dict:
    try:
        date.fromisoformat(month + "-01")
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "invalid month") from exc
    rows = await investment_month_rows(session, user.id, month)
    return ok({"month": month, "items": rows,
               "total_value": str(sum((Decimal(r["closing_value"]) for r in rows if r["closing_value"] is not None), Decimal("0"))),
               "total_profit": str(sum((Decimal(r["profit"]) for r in rows if r["profit"] is not None), Decimal("0"))),
               "complete": bool(rows) and all(r["closing_value"] is not None and r["profit"] is not None for r in rows)})


@router.put("/investments/{item_id}/months/{month}")
async def upsert_investment_month(item_id: int, month: str, body: InvestmentMonthIn,
                                  user: CurrentUser, session: SessionDep) -> dict:
    try:
        date.fromisoformat(month + "-01")
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "invalid month") from exc
    item = await session.scalar(select(InvestmentItem).where(InvestmentItem.id == item_id, InvestmentItem.user_id == user.id))
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "investment not found")
    if month < item.first_month:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "month is before investment start")
    period = await session.scalar(select(InvestmentMonth).where(InvestmentMonth.item_id == item_id, InvestmentMonth.month == month))
    if period is None:
        period = InvestmentMonth(item_id=item_id, month=month)
        session.add(period)
    for key, value in body.model_dump().items():
        setattr(period, key, value)
    await session.commit()
    rows = await investment_month_rows(session, user.id, month)
    return ok(next(r for r in rows if r["id"] == item_id))
