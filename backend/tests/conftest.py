"""Shared test configuration and isolated users in a disposable MySQL database."""

import os
from uuid import uuid4

import pytest

os.environ.setdefault("BCW_JWT_SECRET", "test-secret")
os.environ.setdefault("BCW_FERNET_KEY", "wfd6JLrx2VLDuJfm5RncRzCKqM8M9aFpaSGv4UCh-vM=")


@pytest.fixture
async def upload_db(monkeypatch):
    from sqlalchemy import delete
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import NullPool

    from app.core.config import get_settings
    from app.models.ai import AiCredential, AiStrategy
    from app.models.bill import Bill, UploadTask
    from app.models.category import Category, Tag
    from app.models.invitation import InvitationCode
    from app.models.pipeline import PipelineStep
    from app.models.user import User
    from app.tasks import upload_runner

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
            await session.execute(delete(InvitationCode).where(InvitationCode.created_by == user_id))
            for model in (Bill, UploadTask, PipelineStep, AiStrategy, AiCredential, Category, Tag):
                await session.execute(delete(model).where(model.user_id == user_id))
            await session.execute(delete(User).where(User.id == user_id))
            await session.commit()
        await engine.dispose()
