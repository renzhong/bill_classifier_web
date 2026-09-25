"""Real transaction regressions; never connect to the normal development database."""

from datetime import datetime
from io import BytesIO
from uuid import uuid4

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
from openpyxl import Workbook
from sqlalchemy import select

from app.bills.service import archive_upload_task, classify_upload_task, list_bills, patch_bill
from app.core.security import hash_password
from app.models.bill import Bill, BillTag, UploadTask
from app.models.category import Category, Tag
from app.models.user import User
from app.tasks import upload_runner

pytestmark = pytest.mark.mysql


def csv_bills(order_ids):
    header = "交易时间,交易类型,交易对方,商品,收/支,金额(元),支付方式,当前状态,交易单号,商户单号,备注\n"
    rows = [
        f"2026-01-01 12:00:00,消费,测试店铺,测试商品,支出,18.00,零钱,支付成功,{oid},M1,/\n"
        for oid in order_ids
    ]
    return (header + "".join(rows)).encode()


@pytest.mark.parametrize(
    "invalid_id, expected_note",
    [
        ("first", "1 duplicates"),
        ("x" * 129, "1 data-too-long"),
    ],
)
async def test_invalid_row_does_not_discard_valid_rows(upload_db, invalid_id, expected_note):
    sessions, task_id, user_id = upload_db
    await upload_runner.process_upload(task_id, csv_bills(["first", invalid_id, "last"]))
    async with sessions() as session:
        task = await session.get(UploadTask, task_id)
        orders = set(await session.scalars(select(Bill.order_id).where(Bill.user_id == user_id)))
        assert task.status == "parsed"
        assert task.finished_at is not None
        assert task.total_rows == 3
        assert expected_note in task.error_msg
        assert orders == {"first", "last"}


async def test_long_order_ids_are_imported_after_migration(upload_db):
    sessions, task_id, user_id = upload_db
    order_id = "0" * 65
    await upload_runner.process_upload(task_id, csv_bills([order_id]))
    async with sessions() as session:
        task = await session.get(UploadTask, task_id)
        assert task.status == "parsed"
        assert await session.scalar(select(Bill.order_id).where(Bill.user_id == user_id)) == order_id


async def test_missing_order_id_is_deduplicated_by_exact_parsed_fields(upload_db):
    sessions, task_id, user_id = upload_db
    await upload_runner.process_upload(task_id, csv_bills(["", ""]))
    async with sessions() as session:
        task = await session.get(UploadTask, task_id)
        bills = list(await session.scalars(select(Bill).where(Bill.user_id == user_id)))
        assert len(bills) == 1
        assert bill_order_id_is_missing(bills[0])
        assert "1 duplicates" in task.error_msg


def bill_order_id_is_missing(bill: Bill) -> bool:
    return bill.order_id is None or bill.order_id == ""


async def test_bad_parse_row_is_visible_while_valid_row_survives(upload_db):
    sessions, task_id, user_id = upload_db
    raw = csv_bills(["bad-date", "good-date"]).replace(b"2026-01-01 12:00:00", b"not-a-time", 1)
    await upload_runner.process_upload(task_id, raw)
    async with sessions() as session:
        task = await session.get(UploadTask, task_id)
        assert task.status == "parsed"
        assert len(task.parse_errors) == 1
        assert list(await session.scalars(select(Bill).where(Bill.user_id == user_id)))


async def test_upload_tags_follow_new_bills_and_duplicate_keeps_edits(upload_db):
    sessions, task_id, user_id = upload_db
    async with sessions() as session:
        tag_a = Tag(user_id=user_id, name="甲")
        tag_b = Tag(user_id=user_id, name="乙")
        session.add_all([tag_a, tag_b])
        await session.flush()
        task = await session.get(UploadTask, task_id)
        task.tag_ids = [tag_a.id, tag_b.id]
        tag_a_id, tag_b_id = tag_a.id, tag_b.id
        await session.commit()

    await upload_runner.process_upload(task_id, csv_bills(["tagged-1"]))
    async with sessions() as session:
        bill = await session.scalar(select(Bill).where(Bill.user_id == user_id))
        tags = set(await session.scalars(select(BillTag.tag_id).where(BillTag.bill_id == bill.id)))
        assert tags == {tag_a_id, tag_b_id}
        await session.delete(await session.get(BillTag, (bill.id, tag_b_id)))
        retry = UploadTask(user_id=user_id, source="wechat", filename="again.csv", tag_ids=[tag_b_id])
        session.add(retry)
        await session.commit()
        retry_id = retry.id

    await upload_runner.process_upload(retry_id, csv_bills(["tagged-1"]))
    async with sessions() as session:
        tags = set(await session.scalars(select(BillTag.tag_id).where(BillTag.bill_id == bill.id)))
        assert tags == {tag_a_id}
        second = UploadTask(user_id=user_id, source="wechat", filename="second.csv", tag_ids=[tag_b_id])
        session.add(second)
        await session.commit()
        second_id = second.id

    await upload_runner.process_upload(second_id, csv_bills(["tagged-2"]))
    async with sessions() as session:
        second_bill = await session.scalar(select(Bill).where(Bill.order_id == "tagged-2"))
        second_tags = set(await session.scalars(select(BillTag.tag_id).where(BillTag.bill_id == second_bill.id)))
        assert second_tags == {tag_b_id}


async def test_bill_tag_is_immutable_after_upload(upload_db):
    sessions, task_id, user_id = upload_db
    await upload_runner.process_upload(task_id, csv_bills(["tag-edit-1"]))
    async with sessions() as session:
        bill = await session.scalar(select(Bill).where(Bill.user_id == user_id))
        own_tag = Tag(user_id=user_id, name="我的标签")
        other_user = User(email=f"{uuid4().hex}@example.com", password_hash="unused")
        session.add_all([own_tag, other_user])
        await session.flush()
        other_tag = Tag(user_id=other_user.id, name="别人的标签")
        session.add(other_tag)
        await session.commit()
        bill_id, own_tag_id, other_tag_id, other_user_id = (
            bill.id, own_tag.id, other_tag.id, other_user.id
        )

    try:
        async with sessions() as session:
            with pytest.raises(HTTPException) as exc:
                await patch_bill(session, user_id, bill_id, category_id=None,
                                 category_sent=False, tag_ids=[own_tag_id])
            assert exc.value.status_code == 400
            await archive_upload_task(session, user_id, task_id)
            own_rows, own_count = await list_bills(session, user_id, tag_id=own_tag_id)
            other_rows, other_count = await list_bills(session, user_id, tag_id=other_tag_id)
            assert own_count == 0 and own_rows == []
            assert other_count == 0 and other_rows == []
            with pytest.raises(HTTPException) as exc:
                await patch_bill(session, user_id, bill_id, category_id=None,
                                 category_sent=False, tag_ids=[other_tag_id])
            assert exc.value.status_code == 400

        async with sessions() as session:
            tags = set(await session.scalars(select(BillTag.tag_id).where(BillTag.bill_id == bill_id)))
            assert tags == set()
    finally:
        async with sessions() as session:
            await session.delete(await session.get(Tag, other_tag_id))
            await session.delete(await session.get(User, other_user_id))
            await session.commit()


async def test_manual_category_is_preserved_by_later_classification(upload_db):
    sessions, task_id, user_id = upload_db
    raw = csv_bills(["manual-1"]).replace("测试商品".encode(), "地铁乘车".encode())
    await upload_runner.process_upload(task_id, raw)
    async with sessions() as session:
        manual = Category(user_id=user_id, name="人工分类")
        session.add(manual)
        await session.flush()
        bill = await session.scalar(select(Bill).where(Bill.user_id == user_id))
        await patch_bill(session, user_id, bill.id, category_id=manual.id,
                         category_sent=True, tag_ids=None)
        await classify_upload_task(session, user_id, task_id)
        await session.refresh(bill)
        assert bill.category_id == manual.id
        assert bill.manual_overridden is True

        await patch_bill(session, user_id, bill.id, category_id=None,
                         category_sent=True, tag_ids=None)
        await classify_upload_task(session, user_id, task_id)
        await session.refresh(bill)
        assert bill.category_id is None


async def test_failed_transaction_can_still_mark_task_failed(upload_db, monkeypatch):
    sessions, task_id, _ = upload_db

    async def broken_insert(session, task, items):
        task.owner_label = "x" * 10000
        await session.flush()  # leaves the session requiring rollback

    monkeypatch.setattr(upload_runner, "_insert_bills", broken_insert)
    await upload_runner.process_upload(task_id, csv_bills(["first"]))
    async with sessions() as session:
        task = await session.get(UploadTask, task_id)
        assert task.status == "failed"
        assert task.finished_at is not None
        assert 0 < len(task.error_msg) <= 1024


async def test_upload_does_not_run_pipeline(upload_db, monkeypatch):
    sessions, task_id, user_id = upload_db

    async def broken_classification(*args):
        raise RuntimeError("synthetic classification failure " + "x" * 2000)

    monkeypatch.setattr(upload_runner, "_classify_and_save", broken_classification)
    await upload_runner.process_upload(task_id, csv_bills(["first"]))
    async with sessions() as session:
        task = await session.get(UploadTask, task_id)
        assert task.status == "parsed"
        assert task.error_msg is None
        assert await session.scalar(select(Bill.order_id).where(Bill.user_id == user_id)) == "first"


async def test_login_xlsx_upload_and_duplicate_retry(upload_db):
    from app.core.db import get_session
    from app.main import app

    sessions, _, user_id = upload_db
    async with sessions() as session:
        user = await session.get(User, user_id)
        email = user.email
        user.password_hash = hash_password("synthetic-password")
        await session.commit()

    async def override_session():
        async with sessions() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    workbook = Workbook()
    workbook.active.append(["交易时间", "交易对方", "商品", "收/支", "金额(元)", "当前状态", "交易单号"])
    workbook.active.append(
        [datetime(2026, 1, 1, 12, 0), "测试店铺", "测试商品", "支出", 18, "支付成功", "1" * 65]
    )
    output = BytesIO()
    workbook.save(output)
    workbook.close()
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            denied = await client.post("/api/v1/auth/login", json={"email": email, "password": "wrong"})
            assert denied.status_code == 401
            login = await client.post(
                "/api/v1/auth/login", json={"email": email, "password": "synthetic-password"}
            )
            assert login.status_code == 200
            client.headers["Authorization"] = "Bearer " + login.json()["data"]["access_token"]
            for resource in ("categories", "tags", "dicts"):
                metadata = await client.get(f"/api/v1/{resource}")
                assert metadata.status_code == 200, metadata.text
                assert metadata.json()["data"] == []
            for attempt in range(2):
                response = await client.post(
                    "/api/v1/bills/upload",
                    data={"source": "wechat"},
                    files={
                        "file": (
                            "synthetic.xlsx",
                            output.getvalue(),
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        )
                    },
                )
                assert response.status_code == 200, response.text
                task_id = response.json()["data"]["id"]
                task = (await client.get(f"/api/v1/upload-tasks/{task_id}")).json()["data"]
                assert task["status"] == "parsed"
                if attempt:
                    assert "1 duplicates" in task["error_msg"]
                if not attempt:
                    assert (await client.get("/api/v1/bills")).json()["data"]["total"] == 0
                    archived = await client.post(f"/api/v1/upload-tasks/{task_id}/archive")
                    assert archived.status_code == 200
            bills = (await client.get("/api/v1/bills")).json()["data"]
            assert bills["total"] == 1
            assert bills["items"][0]["order_id"] == "1" * 65
    finally:
        app.dependency_overrides.pop(get_session, None)
