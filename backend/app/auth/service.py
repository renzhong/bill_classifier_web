import secrets
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.models.invitation import InvitationCode
from app.models.user import User
from app.schemas.auth import LoginIn, RegisterIn


async def register_user(session: AsyncSession, body: RegisterIn) -> User:
    invitation = await session.scalar(
        select(InvitationCode).where(InvitationCode.code == body.invitation_code)
    )
    if not invitation:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "invitation code invalid")
    if invitation.used_count >= invitation.max_uses:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "invitation code exhausted")
    if invitation.expires_at:
        now = datetime.now(UTC).replace(tzinfo=None)
        if invitation.expires_at < now:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "invitation code expired")

    existing = await session.scalar(select(User).where(User.email == body.email))
    if existing:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "email already registered")

    user = User(
        email=str(body.email),
        password_hash=hash_password(body.password),
        nickname=body.nickname,
        status="active",
    )
    session.add(user)
    await session.flush()

    invitation.used_count += 1
    if invitation.used_count >= invitation.max_uses:
        invitation.used_by = user.id
        invitation.used_at = datetime.now(UTC).replace(tzinfo=None)

    await session.commit()
    await session.refresh(user)
    return user


async def login(session: AsyncSession, body: LoginIn) -> tuple[str, str, User]:
    user = await session.scalar(select(User).where(User.email == body.email))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid credentials")
    if user.status != "active":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "user inactive")
    return create_access_token(user.id), create_refresh_token(user.id), user


def generate_invitation_code() -> str:
    return secrets.token_urlsafe(9).replace("-", "").replace("_", "")[:12].upper()
