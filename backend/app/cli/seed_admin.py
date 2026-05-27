"""创建首个管理员 + 一条邀请码

用法（容器内）:
    uv run python -m app.cli.seed_admin --email admin@example.com --password xxxxxx [--invitations 3]
"""
import argparse
import asyncio

from sqlalchemy import select

from app.auth.service import generate_invitation_code
from app.core.db import SessionLocal
from app.core.security import hash_password
from app.models.invitation import InvitationCode
from app.models.user import User


async def main(email: str, password: str, invitations: int) -> None:
    async with SessionLocal() as session:
        existing = await session.scalar(select(User).where(User.email == email))
        if existing:
            existing.is_admin = True
            print(f"[seed] user {email} exists, promoted to admin")
            admin = existing
        else:
            admin = User(
                email=email,
                password_hash=hash_password(password),
                nickname="admin",
                status="active",
                is_admin=True,
            )
            session.add(admin)
            await session.flush()
            print(f"[seed] admin {email} created with id={admin.id}")

        for _ in range(invitations):
            code = generate_invitation_code()
            session.add(InvitationCode(code=code, created_by=admin.id, max_uses=1))
            print(f"[seed] invitation code: {code}")

        await session.commit()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--email", required=True)
    p.add_argument("--password", required=True)
    p.add_argument("--invitations", type=int, default=3)
    args = p.parse_args()
    asyncio.run(main(args.email, args.password, args.invitations))
