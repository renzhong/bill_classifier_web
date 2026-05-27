from fastapi import APIRouter, HTTPException, status
from sqlalchemy import delete, select

from app.core.deps import CurrentUser, SessionDep
from app.core.response import ok
from app.models.bill import Bill
from app.models.category import Category
from app.models.dict_entry import UserDictEntry
from app.schemas.meta import CategoryIn, CategoryOut, CategoryPatchIn, CategoryReorderIn

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("")
async def list_categories(user: CurrentUser, session: SessionDep) -> dict:
    rows = (
        await session.scalars(
            select(Category).where(Category.user_id == user.id).order_by(Category.sort_order, Category.id)
        )
    ).all()
    return ok([CategoryOut.model_validate(r).model_dump() for r in rows])


@router.post("")
async def create_category(body: CategoryIn, user: CurrentUser, session: SessionDep) -> dict:
    exists = await session.scalar(
        select(Category).where(Category.user_id == user.id, Category.name == body.name)
    )
    if exists:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "category name already exists")
    cat = Category(user_id=user.id, **body.model_dump())
    session.add(cat)
    await session.commit()
    await session.refresh(cat)
    return ok(CategoryOut.model_validate(cat).model_dump())


@router.patch("/{cat_id}")
async def patch_category(cat_id: int, body: CategoryPatchIn, user: CurrentUser, session: SessionDep) -> dict:
    cat = await session.scalar(select(Category).where(Category.id == cat_id, Category.user_id == user.id))
    if not cat:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "category not found")
    data = body.model_dump(exclude_unset=True)
    if "name" in data and data["name"] != cat.name:
        dup = await session.scalar(
            select(Category).where(Category.user_id == user.id, Category.name == data["name"])
        )
        if dup:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "category name already exists")
    for k, v in data.items():
        setattr(cat, k, v)
    await session.commit()
    await session.refresh(cat)
    return ok(CategoryOut.model_validate(cat).model_dump())


@router.delete("/{cat_id}")
async def delete_category(cat_id: int, user: CurrentUser, session: SessionDep) -> dict:
    cat = await session.scalar(select(Category).where(Category.id == cat_id, Category.user_id == user.id))
    if not cat:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "category not found")
    used_bill = await session.scalar(select(Bill.id).where(Bill.category_id == cat_id).limit(1))
    if used_bill:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "category in use by bills, cannot delete")
    used_entry = await session.scalar(select(UserDictEntry.id).where(UserDictEntry.category_id == cat_id).limit(1))
    if used_entry:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "category referenced by dict entries")
    await session.execute(delete(Category).where(Category.id == cat_id))
    await session.commit()
    return ok({"deleted": cat_id})


@router.post("/reorder")
async def reorder(body: CategoryReorderIn, user: CurrentUser, session: SessionDep) -> dict:
    for entry in body.order:
        cid = int(entry.get("id", 0))
        sort = int(entry.get("sort_order", 0))
        cat = await session.scalar(
            select(Category).where(Category.id == cid, Category.user_id == user.id)
        )
        if cat:
            cat.sort_order = sort
    await session.commit()
    return ok({"reordered": len(body.order)})
