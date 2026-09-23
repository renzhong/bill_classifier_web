"""Real transaction regressions; never connect to the normal development database."""

import os
from datetime import datetime
from io import BytesIO
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from openpyxl import Workbook
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.security import hash_password
from app.models.bill import Bill, UploadTask
from app.models.user import User
from app.tasks import upload_runner

pytestmark = pytest.mark.mysql


@pytest.fixture
async def upload_db(monkeypatch):
    if os.getenv("BCW_TEST_MYSQL") != "1":
        pytest.skip("set BCW_TEST_MYSQL=1 to run against a disposable MySQL database")
    settings = get_settings()
    assert settings.db_name.endswith("_test"), "Refuse to use a non-test database"
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(upload_runner, "SessionLocal", sessions)
    async with sessions() as session:
        user = User(email=f"{uuid4().hex}@example.com", password_hash="unused")
        session.add(user)
        await session.flush()
        task = UploadTask(user_id=user.id, source="wechat", filename="synthetic.csv")
        session.add(task)
        await session.commit()
        user_id, task_id = user.id, task.id
    try:
        yield sessions, task_id, user_id
    finally:
        async with sessions() as session:
            await session.execute(delete(Bill).where(Bill.user_id == user_id))
            await session.execute(delete(UploadTask).where(UploadTask.user_id == user_id))
            await session.execute(delete(User).where(User.id == user_id))
            await session.commit()
        await engine.dispose()


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
        assert task.status == "done"
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
        assert task.status == "done"
        assert await session.scalar(select(Bill.order_id).where(Bill.user_id == user_id)) == order_id


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


async def test_classification_failure_is_visible_and_preserves_import(upload_db, monkeypatch):
    sessions, task_id, user_id = upload_db

    async def broken_classification(*args):
        raise RuntimeError("synthetic classification failure " + "x" * 2000)

    monkeypatch.setattr(upload_runner, "_classify_and_save", broken_classification)
    await upload_runner.process_upload(task_id, csv_bills(["first"]))
    async with sessions() as session:
        task = await session.get(UploadTask, task_id)
        assert task.status == "failed"
        assert 0 < len(task.error_msg) <= 1024
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
                assert task["status"] == "done"
                if attempt:
                    assert "1 duplicates" in task["error_msg"]
            bills = (await client.get("/api/v1/bills")).json()["data"]
            assert bills["total"] == 1
            assert bills["items"][0]["order_id"] == "1" * 65
    finally:
        app.dependency_overrides.pop(get_session, None)
