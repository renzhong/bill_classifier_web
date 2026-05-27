from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.auth.service import generate_invitation_code, login, register_user
from app.core.deps import AdminUser, CurrentUser, SessionDep
from app.core.response import ok
from app.core.security import create_access_token, decode_token
from app.models.invitation import InvitationCode
from app.schemas.auth import (
    InvitationCreateIn,
    InvitationOut,
    LoginIn,
    RefreshIn,
    RegisterIn,
    TokenOut,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register(body: RegisterIn, session: SessionDep) -> dict:
    user = await register_user(session, body)
    return ok(UserOut.model_validate(user).model_dump(mode="json"))


@router.post("/login")
async def login_endpoint(body: LoginIn, session: SessionDep) -> dict:
    access, refresh, _ = await login(session, body)
    return ok(TokenOut(access_token=access, refresh_token=refresh).model_dump())


@router.post("/refresh")
async def refresh_endpoint(body: RefreshIn) -> dict:
    try:
        payload = decode_token(body.refresh_token)
    except ValueError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(e)) from e
    if payload.get("type") != "refresh":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "wrong token type")
    return ok({"access_token": create_access_token(payload["sub"])})


@router.get("/me")
async def me(user: CurrentUser) -> dict:
    return ok(UserOut.model_validate(user).model_dump(mode="json"))


# ===== 邀请码（管理员） =====


@router.get("/invitations")
async def list_invitations(_: AdminUser, session: SessionDep) -> dict:
    rows = (await session.scalars(select(InvitationCode).order_by(InvitationCode.id.desc()))).all()
    return ok([InvitationOut.model_validate(r).model_dump(mode="json") for r in rows])


@router.post("/invitations")
async def create_invitation(
    body: InvitationCreateIn, admin: AdminUser, session: SessionDep
) -> dict:
    code = body.code or generate_invitation_code()
    existing = await session.scalar(select(InvitationCode).where(InvitationCode.code == code))
    if existing:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "code already exists")
    inv = InvitationCode(
        code=code,
        created_by=admin.id,
        max_uses=body.max_uses,
        expires_at=body.expires_at.replace(tzinfo=None) if body.expires_at else None,
    )
    session.add(inv)
    await session.commit()
    await session.refresh(inv)
    return ok(InvitationOut.model_validate(inv).model_dump(mode="json"))
