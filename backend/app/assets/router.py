from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import delete, select

from app.core.deps import CurrentUser, SessionDep
from app.core.response import ok
from app.models.asset import Asset
from app.schemas.finance import AssetIn, AssetOut, AssetPatchIn, CopyAssetsIn

router = APIRouter(prefix="/assets", tags=["assets"])


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


@router.post("")
async def create_asset(body: AssetIn, user: CurrentUser, session: SessionDep) -> dict:
    a = Asset(user_id=user.id, **body.model_dump())
    session.add(a)
    await session.commit()
    await session.refresh(a)
    return ok(AssetOut.model_validate(a).model_dump(mode="json"))


@router.patch("/{asset_id}")
async def patch_asset(
    asset_id: int, body: AssetPatchIn, user: CurrentUser, session: SessionDep
) -> dict:
    a = await session.scalar(select(Asset).where(Asset.id == asset_id, Asset.user_id == user.id))
    if not a:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "asset not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(a, k, v)
    await session.commit()
    await session.refresh(a)
    return ok(AssetOut.model_validate(a).model_dump(mode="json"))


@router.delete("/{asset_id}")
async def delete_asset(asset_id: int, user: CurrentUser, session: SessionDep) -> dict:
    a = await session.scalar(select(Asset).where(Asset.id == asset_id, Asset.user_id == user.id))
    if not a:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "asset not found")
    await session.execute(delete(Asset).where(Asset.id == asset_id))
    await session.commit()
    return ok({"deleted": asset_id})


@router.post("/copy")
async def copy_assets(body: CopyAssetsIn, user: CurrentUser, session: SessionDep) -> dict:
    """把某月的资产快照复制到目标月（金额不变，用户可逐条调整）"""
    src = (
        await session.scalars(
            select(Asset).where(Asset.user_id == user.id, Asset.snapshot_month == body.from_month)
        )
    ).all()
    if not src:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"no assets in {body.from_month}")
    if body.overwrite:
        await session.execute(
            delete(Asset).where(Asset.user_id == user.id, Asset.snapshot_month == body.to_month)
        )
    copied = 0
    for s in src:
        session.add(Asset(
            user_id=user.id,
            snapshot_month=body.to_month,
            asset_type=s.asset_type,
            account_name=s.account_name,
            amount=s.amount,
            remark=s.remark,
        ))
        copied += 1
    await session.commit()
    return ok({"copied": copied, "from": body.from_month, "to": body.to_month})
