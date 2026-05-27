from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class UserDict(Base):
    __tablename__ = "user_dicts"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_user_dict_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(64))
    target_field: Mapped[str] = mapped_column(String(16), default="any")  # payee/item_name/any
    remark: Mapped[str | None] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class UserDictEntry(Base):
    __tablename__ = "user_dict_entries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    dict_id: Mapped[int] = mapped_column(ForeignKey("user_dicts.id", ondelete="CASCADE"), index=True)
    key_text: Mapped[str] = mapped_column(String(255))
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
