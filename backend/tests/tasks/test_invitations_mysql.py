"""Invitation creation and revocation through the public API on a disposable DB."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.db import get_session
from app.core.security import hash_password
from app.main import app
from app.models.user import User

pytestmark = pytest.mark.mysql


async def test_admin_can_revoke_invitation_and_registration_rejects_it(upload_db):
    sessions, _, user_id = upload_db
    async with sessions() as session:
        user = await session.get(User, user_id)
        user.password_hash = hash_password("synthetic-password")
        email = user.email
        await session.commit()

    async def override_session():
        async with sessions() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            login = await client.post("/api/v1/auth/login", json={"email": email, "password": "synthetic-password"})
            client.headers["Authorization"] = "Bearer " + login.json()["data"]["access_token"]
            assert (await client.get("/api/v1/auth/invitations")).status_code == 403

            async with sessions() as session:
                user = await session.get(User, user_id)
                user.is_admin = True
                await session.commit()

            created = await client.post("/api/v1/auth/invitations", json={"max_uses": 2})
            assert created.status_code == 200
            invitation = created.json()["data"]
            assert invitation["revoked_at"] is None
            revoked = await client.post(f"/api/v1/auth/invitations/{invitation['id']}/revoke")
            assert revoked.status_code == 200
            assert revoked.json()["data"]["revoked_at"] is not None

            client.headers.pop("Authorization")
            registration = await client.post("/api/v1/auth/register", json={
                "email": "revoked@example.com",
                "password": "synthetic-password",
                "invitation_code": invitation["code"],
            })
            assert registration.status_code == 400
            assert "revoked" in registration.json()["msg"]
    finally:
        app.dependency_overrides.pop(get_session, None)
