from datetime import date
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.deps import CurrentUser, SessionDep
from app.core.response import ok
from app.investments.router import investment_month_rows
from app.models.asset import Asset, AssetItem, AssetMonthValue
from app.schemas.finance import AssetOut
from app.schemas.monthly_finance import AssetItemIn, AssetItemPatch, AssetValueIn

router = APIRouter(prefix="/assets", tags=["assets"])

monthly_router = APIRouter(tags=["monthly-assets"])


def _item_dict(item: AssetItem) -> dict:
    return {"id": item.id, "name": item.name, "kind": item.kind,
            "active": item.active, "legacy_type": item.legacy_type}


def _check_month(month: str) -> None:
    try:
        date.fromisoformat(month + "-01")
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "invalid month") from exc


async def asset_month_summary(session: SessionDep, user_id: int, month: str) -> dict:
    items = list(await session.scalars(
        select(AssetItem).where(AssetItem.user_id == user_id).order_by(AssetItem.kind, AssetItem.id)
    ))
    values = list(await session.scalars(
        select(AssetMonthValue).where(AssetMonthValue.item_id.in_([i.id for i in items]),
                                      AssetMonthValue.month == month)
    )) if items else []
    by_id = {value.item_id: value for value in values}
    investments = await investment_month_rows(session, user_id, month)
    linked_ids = {i["linked_asset_item_id"] for i in investments if i["linked_asset_item_id"] is not None}
    rows = []
    assets = Decimal("0")
    liabilities = Decimal("0")
    complete = True
    for item in items:
        value = by_id.get(item.id)
        if not item.active and value is None:
            continue
        amount = value.amount if value else None
        included = item.id not in linked_ids
        if amount is None and included:
            complete = False
        elif amount is not None and included and item.kind == "asset":
            assets += amount
        elif amount is not None and included:
            liabilities += amount
        rows.append({**_item_dict(item), "amount": str(amount) if amount is not None else None,
                     "remark": value.remark if value else None, "included_in_total": included})
    if not rows and not investments:
        complete = False
    for investment in investments:
        if investment["closing_value"] is None:
            complete = False
        else:
            assets += Decimal(investment["closing_value"])
    return {"month": month, "items": rows, "investments": investments,
            "asset_total": str(assets), "liability_total": str(liabilities),
            "net_assets": str(assets - liabilities), "complete": complete}


@monthly_router.get("/asset-items")
async def list_asset_items(user: CurrentUser, session: SessionDep) -> dict:
    items = list(await session.scalars(select(AssetItem).where(AssetItem.user_id == user.id).order_by(AssetItem.id)))
    return ok([_item_dict(i) for i in items])


@monthly_router.post("/asset-items")
async def create_asset_item(body: AssetItemIn, user: CurrentUser, session: SessionDep) -> dict:
    item = AssetItem(user_id=user.id, **body.model_dump())
    session.add(item)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "asset item name already exists") from exc
    await session.refresh(item)
    return ok(_item_dict(item))


@monthly_router.patch("/asset-items/{item_id}")
async def patch_asset_item(item_id: int, body: AssetItemPatch, user: CurrentUser, session: SessionDep) -> dict:
    item = await session.scalar(select(AssetItem).where(AssetItem.id == item_id, AssetItem.user_id == user.id))
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "asset item not found")
    for key, value in body.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(item, key, value)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "asset item name already exists") from exc
    await session.refresh(item)
    return ok(_item_dict(item))


@monthly_router.get("/asset-months/{month}")
async def get_asset_month(month: str, user: CurrentUser, session: SessionDep) -> dict:
    _check_month(month)
    return ok(await asset_month_summary(session, user.id, month))


@monthly_router.put("/asset-items/{item_id}/months/{month}")
async def upsert_asset_value(item_id: int, month: str, body: AssetValueIn,
                             user: CurrentUser, session: SessionDep) -> dict:
    _check_month(month)
    item = await session.scalar(select(AssetItem).where(AssetItem.id == item_id, AssetItem.user_id == user.id))
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "asset item not found")
    value = await session.scalar(select(AssetMonthValue).where(
        AssetMonthValue.item_id == item_id, AssetMonthValue.month == month
    ))
    if value is None:
        value = AssetMonthValue(item_id=item_id, month=month)
        session.add(value)
    value.amount = body.amount
    value.remark = body.remark
    await session.commit()
    return ok({"item_id": item_id, "month": month, "amount": str(value.amount), "remark": value.remark})


@router.get("")
async def list_assets(
    user: CurrentUser,
    session: SessionDep,
    month: str | None = Query(default=None, min_length=7, max_length=7),
) -> dict:
    q = select(Asset).where(Asset.user_id == user.id)
    if month:
        q = q.where(Asset.snapshot_month == month)
    q = q.order_by(Asset.snapshot_month.desc(), Asset.asset_type, Asset.id)
    rows = (await session.scalars(q)).all()
    return ok([AssetOut.model_validate(r).model_dump(mode="json") for r in rows])
