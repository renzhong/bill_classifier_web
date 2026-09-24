from __future__ import annotations

import re
from collections.abc import Sequence

from fastapi import HTTPException, status
from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bill import Bill, BillTag, UploadTask
from app.models.category import Category, Tag
from app.schemas.bill import BatchActionIn


async def create_upload_task(
    session: AsyncSession,
    user_id: int,
    source: str,
    filename: str,
    file_size: int,
    tag_ids: list[int],
    owner_label: str | None,
) -> UploadTask:
    if source not in ("alipay", "wechat"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "invalid source")
    if tag_ids:
        valid = (
            await session.scalars(
                select(Tag.id).where(Tag.id.in_(tag_ids), Tag.user_id == user_id)
            )
        ).all()
        if set(valid) != set(tag_ids):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "some tags not found")

    task = UploadTask(
        user_id=user_id,
        source=source,
        filename=filename,
        file_size=file_size,
        status="pending",
        tag_ids=tag_ids,
        owner_label=owner_label,
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


async def list_upload_tasks(session: AsyncSession, user_id: int, limit: int = 50) -> Sequence[UploadTask]:
    return (
        await session.scalars(
            select(UploadTask)
            .where(UploadTask.user_id == user_id)
            .order_by(UploadTask.id.desc())
            .limit(limit)
        )
    ).all()


async def get_upload_task(session: AsyncSession, user_id: int, task_id: int) -> UploadTask:
    task = await session.scalar(
        select(UploadTask).where(UploadTask.id == task_id, UploadTask.user_id == user_id)
    )
    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "task not found")
    return task


async def list_bills(
    session: AsyncSession,
    user_id: int,
    *,
    month: str | None = None,
    source: str | None = None,
    category_id: int | None = None,
    unclassified: bool = False,
    tag_id: int | None = None,
    keyword: str | None = None,
    lifecycle: str | None = None,
    report_expense: bool = False,
    task_id: int | None = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[Bill], int]:
    conds = [Bill.user_id == user_id]
    if task_id is None:
        conds.append(Bill.archived.is_(True))
    else:
        conds.append(Bill.upload_task_id == task_id)
    if month:
        conds.append(Bill.bill_month == month)
    if source:
        conds.append(Bill.source == source)
    if category_id is not None:
        conds.append(Bill.category_id == category_id)
    elif unclassified:
        conds.append(Bill.category_id.is_(None))
    if lifecycle:
        conds.append(Bill.lifecycle == lifecycle)
    if report_expense:
        conds.extend((Bill.bill_type == "expense", Bill.lifecycle.notin_(("skipped", "cross_month_refund"))))
    if keyword:
        like = f"%{keyword}%"
        conds.append(or_(Bill.payee.like(like), Bill.item_name.like(like)))
    if tag_id is not None:
        conds.append(
            Bill.id.in_(select(BillTag.bill_id).where(BillTag.tag_id == tag_id))
        )

    where = and_(*conds)
    total = await session.scalar(select(func.count()).select_from(Bill).where(where)) or 0

    rows = (
        await session.scalars(
            select(Bill)
            .where(where)
            .order_by(Bill.bill_time.desc(), Bill.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return list(rows), int(total)


async def get_bill_with_tags(session: AsyncSession, user_id: int, bill_id: int) -> tuple[Bill, list[int]]:
    bill = await session.scalar(
        select(Bill).where(Bill.id == bill_id, Bill.user_id == user_id)
    )
    if not bill:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "bill not found")
    tag_ids = list(
        await session.scalars(select(BillTag.tag_id).where(BillTag.bill_id == bill.id))
    )
    return bill, tag_ids


async def load_tag_map(session: AsyncSession, bill_ids: list[int]) -> dict[int, list[int]]:
    if not bill_ids:
        return {}
    rows = await session.execute(
        select(BillTag.bill_id, BillTag.tag_id).where(BillTag.bill_id.in_(bill_ids))
    )
    out: dict[int, list[int]] = {bid: [] for bid in bill_ids}
    for bid, tid in rows:
        out.setdefault(bid, []).append(tid)
    return out


async def patch_bill(
    session: AsyncSession, user_id: int, bill_id: int, *, category_id: int | None,
    category_sent: bool, tag_ids: list[int] | None
) -> Bill:
    bill = await session.scalar(select(Bill).where(Bill.id == bill_id, Bill.user_id == user_id))
    if not bill:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "bill not found")
    if tag_ids is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "upload tags cannot be changed")
    if category_sent:
        if category_id is not None:
            await _validate_category_id(session, user_id, category_id)
        bill.category_id = category_id
        bill.manual_overridden = True
        bill.classify_strategy_id = None
        bill.classify_strategy_type = "manual"
        bill.lifecycle = "classified" if category_id is not None else "unprocessed"
    await session.commit()
    await session.refresh(bill)
    return bill


async def batch_action(session: AsyncSession, user_id: int, body: BatchActionIn) -> dict:
    owned = (
        await session.scalars(
            select(Bill.id).where(Bill.id.in_(body.ids), Bill.user_id == user_id)
        )
    ).all()
    if not owned:
        return {"affected": 0}

    if body.action == "delete":
        await session.execute(delete(Bill).where(Bill.id.in_(owned)))
    elif body.action == "set_category":
        cat = body.payload.get("category_id")
        if cat is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "category_id required")
        await _validate_category_id(session, user_id, int(cat))
        for bid in owned:
            b = await session.scalar(select(Bill).where(Bill.id == bid))
            if b:
                b.category_id = cat
                b.manual_overridden = True
                if b.lifecycle == "unprocessed":
                    b.lifecycle = "classified"
    elif body.action == "add_tag":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "upload tags cannot be changed")
    elif body.action == "remove_tag":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "upload tags cannot be changed")

    await session.commit()
    return {"affected": len(owned)}


async def _validate_tag_ids(session: AsyncSession, user_id: int, tag_ids: list[int]) -> None:
    if not tag_ids:
        return
    owned_ids = set(await session.scalars(
        select(Tag.id).where(Tag.user_id == user_id, Tag.id.in_(tag_ids))
    ))
    if owned_ids != set(tag_ids):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "some tags not found")


async def _validate_category_id(session: AsyncSession, user_id: int, category_id: int) -> None:
    found = await session.scalar(
        select(Category.id).where(Category.id == category_id, Category.user_id == user_id)
    )
    if found is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "category not found")


async def classify_upload_task(session: AsyncSession, user_id: int, task_id: int) -> UploadTask:
    task = await session.scalar(
        select(UploadTask).where(UploadTask.id == task_id, UploadTask.user_id == user_id).with_for_update()
    )
    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "task not found")
    if task.status not in ("parsed", "classified"):
        raise HTTPException(status.HTTP_409_CONFLICT, "task is not ready for classification")
    bills = list(await session.scalars(
        select(Bill).where(Bill.upload_task_id == task_id, Bill.user_id == user_id, Bill.archived.is_(False))
    ))
    matches = [b for b in bills if not b.manual_overridden and b.bill_type == "expense"
               and re.search(r"地铁|公交", b.item_name or "")]
    category = None
    if matches:
        category = await session.scalar(
            select(Category).where(Category.user_id == user_id, Category.name == "交通")
        )
        if category is None:
            category = Category(user_id=user_id, name="交通", display_name="交通")
            session.add(category)
            await session.flush()
    for bill in matches:
        bill.category_id = category.id if category else None
        bill.classify_strategy_id = None
        bill.classify_strategy_type = "name_regex"
        bill.lifecycle = "classified"
    task.classified_rows = sum(1 for b in bills if b.category_id is not None)
    task.status = "classified"
    await session.commit()
    await session.refresh(task)
    return task


async def archive_upload_task(session: AsyncSession, user_id: int, task_id: int) -> UploadTask:
    task = await session.scalar(
        select(UploadTask).where(UploadTask.id == task_id, UploadTask.user_id == user_id).with_for_update()
    )
    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "task not found")
    if task.status == "archived":
        return task
    if task.status not in ("parsed", "classified"):
        raise HTTPException(status.HTTP_409_CONFLICT, "task is not ready for archive")
    await session.execute(
        update(Bill)
        .where(Bill.upload_task_id == task_id, Bill.user_id == user_id)
        .values(archived=True)
    )
    task.status = "archived"
    await session.commit()
    await session.refresh(task)
    return task
