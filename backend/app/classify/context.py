"""Pipeline 执行上下文：把 user_id、DB session、类别表、AI service 等依赖注入给 StrategyType"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.category import Category


@dataclass
class ClassifyContext:
    user_id: int
    session: AsyncSession
    step_id: int                              # 当前 pipeline_step.id
    categories: list[Category] = field(default_factory=list)
    extras: dict[str, Any] = field(default_factory=dict)
