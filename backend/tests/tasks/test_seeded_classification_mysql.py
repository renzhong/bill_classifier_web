"""The same SQL and files used for manual testing exercise the real pipeline."""

import csv
from decimal import Decimal
from io import StringIO

import pymysql
import pytest
from cryptography.fernet import Fernet
from pymysql.constants import CLIENT
from sqlalchemy import select

from app.ai import service
from app.core.config import get_settings
from app.core.security import encrypt_secret
from app.models.ai import AiCredential, AiStrategy
from app.models.bill import Bill, UploadTask
from app.models.category import Category
from app.models.pipeline import PipelineStep
from app.tasks import upload_runner
from devdata.generate import DATA_DIR, cases, rows, xlsx_bytes

pytestmark = pytest.mark.mysql


@pytest.mark.parametrize("source", ["wechat", "alipay"])
@pytest.mark.parametrize("extension", ["csv", "xlsx"])
async def test_seeded_upload_classifies_and_deduplicates(upload_db, monkeypatch, source, extension):
    sessions, task_id, user_id = upload_db
    settings = get_settings()
    with pymysql.connect(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_password,
        database=settings.db_name,
        charset="utf8mb4",
        client_flag=CLIENT.MULTI_STATEMENTS,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SET @fixture_user_id = %s", (user_id,))
            cursor.execute((DATA_DIR / "seed.sql").read_text())
            while cursor.nextset():
                pass
        connection.commit()

    monkeypatch.setattr(settings, "fernet_key", Fernet.generate_key().decode())
    async with sessions() as session:
        credential = AiCredential(
            user_id=user_id,
            provider="openai",
            model_name="fixture-model",
            api_key_encrypted=encrypt_secret("synthetic-key"),
            enabled=True,
        )
        session.add(credential)
        await session.flush()
        strategy = await session.scalar(select(AiStrategy).where(AiStrategy.user_id == user_id))
        strategy.credential_id = credential.id
        step = await session.scalar(select(PipelineStep).where(PipelineStep.user_id == user_id))
        step.enabled = True
        task = await session.get(UploadTask, task_id)
        task.source = source
        task.filename = f"synthetic.{extension}"
        await session.commit()

    samples = cases()
    calls = []

    class RecordedProvider:
        async def chat(self, *, prompt, model, api_key, base_url):
            assert model == "fixture-model" and api_key == "synthetic-key"
            assert "餐厅、早餐、咖啡归为餐饮" in prompt
            assert all(f"- {category}\n" in prompt for category in ("餐饮", "交通", "购物"))
            payee = next(
                line.removeprefix("- 收款方: ")
                for line in prompt.splitlines()
                if line.startswith("- 收款方: ")
            )
            calls.append(payee)
            return next(case["expected_category"] or "UNKNOWN" for case in samples if case["payee"] == payee)

    monkeypatch.setattr(service, "get_provider", lambda key: RecordedProvider())
    if extension == "xlsx":
        content = xlsx_bytes(source)
    else:
        output = StringIO()
        csv.writer(output).writerows(rows(source))
        content = output.getvalue().encode("gbk" if source == "alipay" else "utf-8-sig")

    await upload_runner.process_upload(task_id, content)
    async with sessions() as session:
        task = await session.get(UploadTask, task_id)
        assert (task.status, task.total_rows, task.classified_rows) == ("done", 6, 5)
        actual = (
            await session.execute(
                select(Bill, Category.name)
                .outerjoin(Category, Bill.category_id == Category.id)
                .where(Bill.user_id == user_id)
            )
        ).all()
        by_order = {bill.order_id: (bill, category) for bill, category in actual}
        assert len(by_order) == 6
        for case in samples:
            bill, category = by_order[case["order_id"]]
            assert bill.amount == Decimal(case["expected_amount"])
            assert category == case["expected_category"]
            assert bill.lifecycle == ("classified" if category else "unprocessed")
        retry = UploadTask(user_id=user_id, source=source, filename=task.filename)
        session.add(retry)
        await session.commit()
        retry_id = retry.id

    await upload_runner.process_upload(retry_id, content)
    async with sessions() as session:
        retry = await session.get(UploadTask, retry_id)
        assert retry.status == "done"
        assert "6 duplicates" in retry.error_msg
        assert len(calls) == 6  # Duplicate imports must not call a model again.
