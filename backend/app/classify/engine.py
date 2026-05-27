"""Pipeline 执行引擎：按 user 的启用步骤顺序依次跑 StrategyType.run"""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.classify.bill_item import ClassifyBillItem
from app.classify.context import ClassifyContext
from app.classify.strategy_types import REGISTRY
from app.models.category import Category
from app.models.pipeline import PipelineStep

logger = logging.getLogger(__name__)


async def load_pipeline(session: AsyncSession, user_id: int) -> list[PipelineStep]:
    return list(
        await session.scalars(
            select(PipelineStep)
            .where(PipelineStep.user_id == user_id, PipelineStep.enabled.is_(True))
            .order_by(PipelineStep.sort_order, PipelineStep.id)
        )
    )


async def run_pipeline(
    session: AsyncSession,
    user_id: int,
    items: list[ClassifyBillItem],
) -> list[ClassifyBillItem]:
    if not items:
        return items

    steps = await load_pipeline(session, user_id)
    if not steps:
        return items

    categories = list(
        await session.scalars(select(Category).where(Category.user_id == user_id))
    )

    for step in steps:
        strategy = REGISTRY.get(step.strategy_type)
        if not strategy:
            logger.warning("pipeline_step %s: unknown strategy_type %s", step.id, step.strategy_type)
            continue
        ctx = ClassifyContext(
            user_id=user_id,
            session=session,
            step_id=step.id,
            categories=categories,
        )
        try:
            items = await strategy.run(items, step.params or {}, ctx)
        except Exception:
            logger.exception("strategy %s (step %s) failed", step.strategy_type, step.id)
            # 单个 step 失败不中断后续；可见错误已记录
    return items
