"""唯一内置 StrategyType：调 LLM 给账单分类"""
from __future__ import annotations

import asyncio
import logging
from decimal import Decimal

from sqlalchemy import select

from app.ai.base import ProviderError
from app.ai.service import classify_one
from app.classify.bill_item import ClassifyBillItem
from app.classify.context import ClassifyContext
from app.classify.strategy_types.base import StrategyType
from app.models.ai import AiCredential, AiStrategy

logger = logging.getLogger(__name__)


class AiClassifyStrategy(StrategyType):
    type_key = "ai_classify"
    display_name = "AI 分类"
    description = (
        "调用大模型分类账单。把用户在「AI 策略」中填写的多条文本规则拼入 prompt，"
        "对每一条待分类账单单独发起一次推理。"
    )
    param_schema = {
        "type": "object",
        "required": ["strategy_id"],
        "properties": {
            "strategy_id": {
                "type": "integer",
                "title": "AI 策略",
                "description": "选择 /settings/ai/strategies 中的一条策略",
            },
            "only_unclassified": {
                "type": "boolean",
                "title": "仅对未分类账单生效",
                "default": True,
            },
            "max_concurrency": {
                "type": "integer",
                "title": "并发上限",
                "default": 4,
                "minimum": 1,
                "maximum": 32,
            },
        },
    }

    async def validate_params_with_session(self, params: dict, *, session, user_id: int) -> None:
        sid = params.get("strategy_id")
        if not isinstance(sid, int):
            raise ValueError("strategy_id required")
        strategy = await session.scalar(
            select(AiStrategy).where(AiStrategy.id == sid, AiStrategy.user_id == user_id)
        )
        if not strategy:
            raise ValueError(f"ai_strategy {sid} not found")
        if not strategy.credential_id:
            raise ValueError("ai_strategy has no credential bound")
        cred = await session.scalar(
            select(AiCredential).where(
                AiCredential.id == strategy.credential_id, AiCredential.user_id == user_id
            )
        )
        if not cred:
            raise ValueError("ai_credential not found")

    def validate_params(self, params: dict) -> None:
        sid = params.get("strategy_id")
        if not isinstance(sid, int):
            raise ValueError("strategy_id required and must be an integer")
        c = params.get("max_concurrency", 4)
        if not isinstance(c, int) or not (1 <= c <= 32):
            raise ValueError("max_concurrency must be an int in [1, 32]")

    async def run(
        self,
        items: list[ClassifyBillItem],
        params: dict,
        ctx: ClassifyContext,
    ) -> list[ClassifyBillItem]:
        strategy_id = params["strategy_id"]
        only_unclassified = params.get("only_unclassified", True)
        concurrency = int(params.get("max_concurrency", 4))

        targets = [
            it for it in items
            if not it.manual_overridden
            and ((not only_unclassified) or (not it.is_terminal and it.category_id is None))
        ]
        if not targets:
            return items

        # 加载 strategy 关联的 provider 信息
        strategy = await ctx.session.scalar(
            select(AiStrategy).where(
                AiStrategy.id == strategy_id, AiStrategy.user_id == ctx.user_id
            )
        )
        if not strategy:
            logger.warning("ai_strategy %s not found, skipping", strategy_id)
            return items
        provider_key: str | None = None
        if strategy.credential_id:
            cred = await ctx.session.scalar(
                select(AiCredential).where(AiCredential.id == strategy.credential_id)
            )
            provider_key = cred.provider if cred else None

        name_to_cat = {c.name: c for c in ctx.categories}
        sem = asyncio.Semaphore(concurrency)

        async def _one(item: ClassifyBillItem) -> None:
            async with sem:
                try:
                    res = await classify_one(
                        ctx.session,
                        user_id=ctx.user_id,
                        strategy_id=strategy_id,
                        bill=item,
                        categories=ctx.categories,
                    )
                except ProviderError as e:
                    logger.warning("ai_classify bill %s failed: %s", item.id, e)
                    return
                if res.category and res.category in name_to_cat:
                    item.category_id = name_to_cat[res.category].id
                    item.classify_strategy_id = ctx.step_id
                    item.classify_strategy_type = self.type_key
                    item.lifecycle = "classified"
                    item.ai_provider = provider_key
                    item.ai_confidence = res.confidence or Decimal("0.80")

        await asyncio.gather(*(_one(t) for t in targets))
        return items
