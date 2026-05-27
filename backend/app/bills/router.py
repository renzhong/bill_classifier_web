from __future__ import annotations

import json

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, Query, UploadFile, status

from app.bills.service import (
    batch_action,
    create_upload_task,
    get_bill_with_tags,
    get_upload_task,
    list_bills,
    list_upload_tasks,
    load_tag_map,
    patch_bill,
)
from app.core.config import get_settings
from app.core.deps import CurrentUser, SessionDep
from app.core.response import ok
from app.schemas.bill import BatchActionIn, BillListOut, BillOut, BillPatchIn, UploadTaskOut
from app.tasks.upload_runner import process_upload

router = APIRouter(tags=["bills"])

_settings = get_settings()


@router.post("/bills/upload")
async def upload_bill(
    user: CurrentUser,
    session: SessionDep,
    background: BackgroundTasks,
    file: UploadFile = File(...),
    source: str = Form(...),
    owner_label: str | None = Form(default=None),
    tag_ids: str = Form(default="[]"),
) -> dict:
    raw = await file.read()
    if len(raw) > _settings.upload_max_bytes:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "file too large")
    try:
        tag_id_list = json.loads(tag_ids) if isinstance(tag_ids, str) else (tag_ids or [])
        if not isinstance(tag_id_list, list):
            raise ValueError
        tag_id_list = [int(t) for t in tag_id_list]
    except (ValueError, TypeError) as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"invalid tag_ids: {e}") from e

    task = await create_upload_task(
        session=session,
        user_id=user.id,
        source=source,
        filename=file.filename or "uploaded.csv",
        file_size=len(raw),
        tag_ids=tag_id_list,
        owner_label=owner_label,
    )
    background.add_task(process_upload, task.id, raw)
    return ok(UploadTaskOut.model_validate(task).model_dump(mode="json"))


@router.get("/upload-tasks")
async def list_tasks_endpoint(user: CurrentUser, session: SessionDep) -> dict:
    rows = await list_upload_tasks(session, user.id)
    return ok([UploadTaskOut.model_validate(r).model_dump(mode="json") for r in rows])


@router.get("/upload-tasks/{task_id}")
async def get_task_endpoint(task_id: int, user: CurrentUser, session: SessionDep) -> dict:
    task = await get_upload_task(session, user.id, task_id)
    return ok(UploadTaskOut.model_validate(task).model_dump(mode="json"))


@router.get("/bills")
async def list_bills_endpoint(
    user: CurrentUser,
    session: SessionDep,
    month: str | None = Query(default=None),
    source: str | None = Query(default=None),
    category_id: int | None = Query(default=None),
    tag_id: int | None = Query(default=None),
    keyword: str | None = Query(default=None),
    lifecycle: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
) -> dict:
    rows, total = await list_bills(
        session,
        user.id,
        month=month,
        source=source,
        category_id=category_id,
        tag_id=tag_id,
        keyword=keyword,
        lifecycle=lifecycle,
        page=page,
        page_size=page_size,
    )
    tag_map = await load_tag_map(session, [r.id for r in rows])
    items = []
    for b in rows:
        d = BillOut.model_validate(b).model_dump(mode="json")
        d["tag_ids"] = tag_map.get(b.id, [])
        items.append(d)
    return ok(BillListOut(items=items, total=total, page=page, page_size=page_size).model_dump(mode="json"))


@router.get("/bills/{bill_id}")
async def get_bill_endpoint(bill_id: int, user: CurrentUser, session: SessionDep) -> dict:
    bill, tag_ids = await get_bill_with_tags(session, user.id, bill_id)
    d = BillOut.model_validate(bill).model_dump(mode="json")
    d["tag_ids"] = tag_ids
    return ok(d)


@router.patch("/bills/{bill_id}")
async def patch_bill_endpoint(
    bill_id: int, body: BillPatchIn, user: CurrentUser, session: SessionDep
) -> dict:
    bill = await patch_bill(
        session, user.id, bill_id, category_id=body.category_id, tag_ids=body.tag_ids
    )
    _, tag_ids = await get_bill_with_tags(session, user.id, bill.id)
    d = BillOut.model_validate(bill).model_dump(mode="json")
    d["tag_ids"] = tag_ids
    return ok(d)


@router.post("/bills/{bill_id}/reclassify")
async def reclassify_endpoint(bill_id: int, user: CurrentUser, session: SessionDep) -> dict:
    # M3 接入分类引擎；MVP 当前阶段返回占位
    _, _ = await get_bill_with_tags(session, user.id, bill_id)
    return ok({"queued": False, "note": "reclassify available after M3"})


@router.post("/bills/batch")
async def batch_endpoint(body: BatchActionIn, user: CurrentUser, session: SessionDep) -> dict:
    return ok(await batch_action(session, user.id, body))
