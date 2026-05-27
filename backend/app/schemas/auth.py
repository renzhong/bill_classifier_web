from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    nickname: str | None = Field(default=None, max_length=64)
    invitation_code: str = Field(min_length=4, max_length=32)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshIn(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    nickname: str | None
    is_admin: bool
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class InvitationCreateIn(BaseModel):
    code: str | None = Field(default=None, max_length=32)
    max_uses: int = Field(default=1, ge=1, le=1000)
    expires_at: datetime | None = None


class InvitationOut(BaseModel):
    id: int
    code: str
    max_uses: int
    used_count: int
    expires_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
