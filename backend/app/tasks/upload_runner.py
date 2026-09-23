"""上传账单后台处理：解析 CSV → 落 bills → 跑 Pipeline → 回写分类结果"""
from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.exc import DataError, IntegrityError

from app.classify.bill_item import ClassifyBillItem
from app.classify.engine import run_pipeline
from app.core.db import SessionLocal
from app.models.bill import Bill, UploadTask
from app.parsers.base import ParseError
from app.parsers.dispatch import parse_upload

logger = logging.getLogger(__name__)


async def process_upload(task_id: int, file_bytes: bytes) -> None:
    """异步解析 + 落库 + 跑 Pipeline。每个阶段失败都把 upload_task 标对应状态。"""
    async with SessionLocal() as session:
        task = await session.scalar(select(UploadTask).where(UploadTask.id == task_id))
        if not task:
            logger.warning("upload_task %s vanished", task_id)
            return

        task.status = "parsing"
        await session.commit()

        try:
            result = parse_upload(
                file_bytes,
                filename=task.filename or "",
                declared_source=task.source,
                owner=task.owner_label,
            )
        except ParseError as e:
            await _mark_failed(session, task_id, f"parse error: {e}")
            return
        except Exception as e:  # pragma: no cover
            logger.exception("unexpected parse failure for task %s", task_id)
            await _mark_failed(session, task_id, f"unexpected: {e}")
            return

        try:
            inserted_bills, skipped_duplicate, skipped_data, first_data_err = \
                await _insert_bills(session, task, result.items)
            await session.commit()

            # 跑分类 pipeline（用户没配置 step 时 run_pipeline 直接返回）
            classified = 0
            if inserted_bills:
                task.status = "classifying"
                await session.commit()
                classified = await _classify_and_save(session, task.user_id, inserted_bills)

            task.total_rows = len(result.items)
            task.classified_rows = classified
            task.status = "done"
            notes = []
            if result.skipped_rows:
                notes.append(f"skipped {result.skipped_rows} bad rows")
            if skipped_duplicate:
                notes.append(f"skipped {skipped_duplicate} duplicates")
            if skipped_data:
                notes.append(f"skipped {skipped_data} data-too-long ({first_data_err})")
            if result.errors:
                notes.append(f"errors: {len(result.errors)} (first: {result.errors[0][:120]})")
            task.error_msg = "; ".join(notes)[:1024] if notes else None
            task.finished_at = datetime.now(UTC).replace(tzinfo=None)
            await session.commit()
            logger.info(
                "upload_task %s done: inserted=%d classified=%d dup=%d data_err=%d",
                task_id, len(inserted_bills), classified, skipped_duplicate, skipped_data,
            )
        except Exception as e:  # 兜底：任何未预期错误都把 task 标 failed，避免悬挂在 parsing
            logger.exception("post-parse failure for task %s", task_id)
            await _mark_failed(session, task_id, f"post-parse: {e}")
            return


async def _insert_bills(session, task: UploadTask, items: list) -> tuple[list[Bill], int, int, str | None]:
    """逐条插 bill，重复 / 数据过长都跳过；返回 (inserted, dup_count, data_err_count, first_data_err)"""
    inserted: list[Bill] = []
    skipped_duplicate = 0
    skipped_data = 0
    first_data_err: str | None = None
    for item in items:
        bill = Bill(
            user_id=task.user_id,
            upload_task_id=task.id,
            source=item.source,
            owner=item.owner,
            order_id=item.order_id,
            payee=item.payee,
            item_name=item.item_name,
            amount=item.amount,
            bill_type=item.bill_type,
            bill_time=item.bill_time,
            lifecycle="unprocessed",
        )
        try:
            async with session.begin_nested():
                session.add(bill)
                await session.flush()
            inserted.append(bill)
        except IntegrityError:
            skipped_duplicate += 1
        except DataError as e:
            skipped_data += 1
            if first_data_err is None:
                first_data_err = str(e.orig)[:120]
            logger.warning("bill skipped due to DataError (order_id=%r): %s", item.order_id, e.orig)
    return inserted, skipped_duplicate, skipped_data, first_data_err


async def _mark_failed(session, task_id: int, msg: str) -> None:
    # A failed flush must be rolled back before recording a terminal status.
    # Use the saved ID because rollback expires ORM instances in async sessions.
    await session.rollback()
    await session.execute(
        update(UploadTask)
        .where(UploadTask.id == task_id)
        .values(status="failed", error_msg=msg[:1024], finished_at=datetime.now(UTC).replace(tzinfo=None))
    )
    await session.commit()


async def _classify_and_save(session, user_id: int, bills: list[Bill]) -> int:
    items = [_bill_to_item(b) for b in bills]
    items = await run_pipeline(session, user_id, items)
    classified = 0
    by_id = {b.id: b for b in bills}
    for it in items:
        b = by_id.get(it.id)
        if not b:
            continue
        if it.category_id is not None or it.lifecycle != "unprocessed":
            b.category_id = it.category_id
            b.classify_strategy_id = it.classify_strategy_id
            b.classify_strategy_type = it.classify_strategy_type
            b.lifecycle = it.lifecycle if it.lifecycle != "unprocessed" else b.lifecycle
            b.skip_reason = it.skip_reason
            b.ai_provider = it.ai_provider
            b.ai_confidence = it.ai_confidence
            if it.category_id is not None:
                classified += 1
    await session.commit()
    return classified


def _bill_to_item(b: Bill) -> ClassifyBillItem:
    return ClassifyBillItem(
        id=b.id,
        source=b.source,
        payee=b.payee,
        item_name=b.item_name,
        amount=b.amount,
        bill_type=b.bill_type,  # type: ignore[arg-type]
        bill_time=b.bill_time,
        owner=b.owner,
        order_id=b.order_id,
        category_id=b.category_id,
        classify_strategy_id=b.classify_strategy_id,
        classify_strategy_type=b.classify_strategy_type,
        lifecycle=b.lifecycle,
    )


async def reclassify_one(user_id: int, bill_id: int) -> bool:
    """单条账单重新跑 Pipeline；返回是否命中分类"""
    async with SessionLocal() as session:
        bill = await session.scalar(
            select(Bill).where(Bill.id == bill_id, Bill.user_id == user_id)
        )
        if not bill:
            return False
        # 重新跑前清掉之前的分类结果（手工标记不被重置）
        if not bill.manual_overridden:
            bill.category_id = None
            bill.classify_strategy_id = None
            bill.classify_strategy_type = None
            bill.lifecycle = "unprocessed"
            bill.skip_reason = None
            bill.ai_provider = None
            bill.ai_confidence = None
            await session.commit()

        classified = await _classify_and_save(session, user_id, [bill])
        return classified > 0
