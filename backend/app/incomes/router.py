from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import delete, select

from app.core.deps import CurrentUser, SessionDep
from app.core.response import ok
from app.models.income import MonthlyIncome
from app.schemas.finance import IncomeIn, IncomeOut, IncomePatchIn

router = APIRouter(prefix="/incomes", tags=["incomes"])


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
