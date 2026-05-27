"""上传账单后台处理：解析 CSV → 入 bills 表（暂不分类，分类在 M3 接入）"""
from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.db import SessionLocal
from app.models.bill import Bill, UploadTask
from app.parsers import get_parser
from app.parsers.base import ParseError

logger = logging.getLogger(__name__)


async def process_upload(task_id: int, file_bytes: bytes) -> None:
    """异步解析 + 落库。任何阶段失败都把 upload_task 标 failed。"""
    async with SessionLocal() as session:
        task = await session.scalar(select(UploadTask).where(UploadTask.id == task_id))
        if not task:
            logger.warning("upload_task %s vanished", task_id)
            return

        task.status = "parsing"
        await session.commit()

        try:
            parser = get_parser(task.source)
            result = parser.parse(file_bytes, owner=task.owner_label)
        except ParseError as e:
            task.status = "failed"
            task.error_msg = f"parse error: {e}"
            task.finished_at = datetime.now(UTC).replace(tzinfo=None)
            await session.commit()
            return
        except Exception as e:  # pragma: no cover
            logger.exception("unexpected parse failure for task %s", task_id)
            task.status = "failed"
            task.error_msg = f"unexpected: {e}"
            task.finished_at = datetime.now(UTC).replace(tzinfo=None)
            await session.commit()
            return

        skipped_duplicate = 0
        inserted = 0
        for item in result.items:
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
            session.add(bill)
            try:
                await session.flush()
                inserted += 1
            except IntegrityError:
                await session.rollback()
                skipped_duplicate += 1

        task.total_rows = len(result.items)
        task.classified_rows = 0  # M3 分类后再填
        task.status = "done"
        notes = []
        if result.skipped_rows:
            notes.append(f"skipped {result.skipped_rows} bad rows")
        if skipped_duplicate:
            notes.append(f"skipped {skipped_duplicate} duplicates")
        if result.errors:
            notes.append(f"errors: {len(result.errors)} (first: {result.errors[0][:120]})")
        task.error_msg = "; ".join(notes) if notes else None
        task.finished_at = datetime.now(UTC).replace(tzinfo=None)
        await session.commit()
        logger.info("upload_task %s done: inserted=%d skipped_dup=%d", task_id, inserted, skipped_duplicate)
