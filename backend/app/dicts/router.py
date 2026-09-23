import csv
import io

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import delete, func, select

from app.core.deps import CurrentUser, SessionDep
from app.core.response import ok
from app.models.category import Category
from app.models.dict_entry import UserDict, UserDictEntry
from app.schemas.meta import (
    DictBulkImportIn,
    DictEntryIn,
    DictEntryOut,
    DictIn,
    DictOut,
    DictPatchIn,
)

router = APIRouter(prefix="/dicts", tags=["dicts"])


async def _own_dict(session, user_id: int, dict_id: int) -> UserDict:
    d = await session.scalar(
        select(UserDict).where(UserDict.id == dict_id, UserDict.user_id == user_id)
    )
    if not d:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "dict not found")
    return d


@router.get("")
async def list_dicts(user: CurrentUser, session: SessionDep) -> dict:
    rows = (
        await session.scalars(
            select(UserDict).where(UserDict.user_id == user.id).order_by(UserDict.id)
        )
    ).all()
    counts_rows = await session.execute(
        select(UserDictEntry.dict_id, func.count(UserDictEntry.id))
        .where(UserDictEntry.dict_id.in_([d.id for d in rows]))
        .group_by(UserDictEntry.dict_id)
    )
    counts = {did: cnt for did, cnt in counts_rows}
    out = []
    for d in rows:
        item = DictOut.model_validate(d).model_dump()
        item["entry_count"] = counts.get(d.id, 0)
        out.append(item)
    return ok(out)


@router.post("")
async def create_dict(body: DictIn, user: CurrentUser, session: SessionDep) -> dict:
    dup = await session.scalar(
        select(UserDict).where(UserDict.user_id == user.id, UserDict.name == body.name)
    )
    if dup:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "dict name already exists")
    d = UserDict(user_id=user.id, **body.model_dump())
    session.add(d)
    await session.commit()
    await session.refresh(d)
    return ok({**DictOut.model_validate(d).model_dump(), "entry_count": 0})


@router.patch("/{dict_id}")
async def patch_dict(dict_id: int, body: DictPatchIn, user: CurrentUser, session: SessionDep) -> dict:
    d = await _own_dict(session, user.id, dict_id)
    data = body.model_dump(exclude_unset=True)
    if "name" in data and data["name"] != d.name:
        dup = await session.scalar(
            select(UserDict).where(UserDict.user_id == user.id, UserDict.name == data["name"])
        )
        if dup:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "dict name already exists")
    for k, v in data.items():
        setattr(d, k, v)
    await session.commit()
    await session.refresh(d)
    return ok(DictOut.model_validate(d).model_dump())


@router.delete("/{dict_id}")
async def delete_dict(dict_id: int, user: CurrentUser, session: SessionDep) -> dict:
    await _own_dict(session, user.id, dict_id)
    await session.execute(delete(UserDict).where(UserDict.id == dict_id))
    await session.commit()
    return ok({"deleted": dict_id})


@router.get("/{dict_id}/entries")
async def list_entries(dict_id: int, user: CurrentUser, session: SessionDep) -> dict:
    await _own_dict(session, user.id, dict_id)
    rows = (
        await session.scalars(
            select(UserDictEntry).where(UserDictEntry.dict_id == dict_id).order_by(UserDictEntry.id)
        )
    ).all()
    return ok([DictEntryOut.model_validate(r).model_dump() for r in rows])


@router.post("/{dict_id}/entries")
async def create_entry(
    dict_id: int, body: DictEntryIn, user: CurrentUser, session: SessionDep
) -> dict:
    await _own_dict(session, user.id, dict_id)
    cat = await session.scalar(
        select(Category).where(Category.id == body.category_id, Category.user_id == user.id)
    )
    if not cat:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "category not found")
    entry = UserDictEntry(dict_id=dict_id, key_text=body.key_text, category_id=body.category_id)
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return ok(DictEntryOut.model_validate(entry).model_dump())


@router.delete("/{dict_id}/entries/{entry_id}")
async def delete_entry(dict_id: int, entry_id: int, user: CurrentUser, session: SessionDep) -> dict:
    await _own_dict(session, user.id, dict_id)
    entry = await session.scalar(
        select(UserDictEntry).where(UserDictEntry.id == entry_id, UserDictEntry.dict_id == dict_id)
    )
    if not entry:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "entry not found")
    await session.execute(delete(UserDictEntry).where(UserDictEntry.id == entry_id))
    await session.commit()
    return ok({"deleted": entry_id})


@router.post("/{dict_id}/entries/bulk")
async def bulk_import(
    dict_id: int, body: DictBulkImportIn, user: CurrentUser, session: SessionDep
) -> dict:
    """每行 "key,category_name"，空行与 # 注释忽略；找不到 category 整批失败"""
    await _own_dict(session, user.id, dict_id)

    cats = (await session.scalars(select(Category).where(Category.user_id == user.id))).all()
    name_to_id = {c.name: c.id for c in cats}

    reader = csv.reader(io.StringIO(body.csv_text))
    pending: list[UserDictEntry] = []
    errors: list[str] = []
    for line_no, row in enumerate(reader, start=1):
        if not row or not row[0].strip() or row[0].strip().startswith("#"):
            continue
        if len(row) < 2:
            errors.append(f"line {line_no}: need at least 2 columns")
            continue
        key, cat_name = row[0].strip(), row[1].strip()
        if cat_name not in name_to_id:
            errors.append(f"line {line_no}: category '{cat_name}' not found")
            continue
        pending.append(UserDictEntry(dict_id=dict_id, key_text=key, category_id=name_to_id[cat_name]))

    if errors:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "; ".join(errors))

    session.add_all(pending)
    await session.commit()
    return ok({"inserted": len(pending)})
