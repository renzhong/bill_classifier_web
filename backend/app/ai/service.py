"""AI 业务层：根据 user / strategy 取出 credential、解密 key、调 provider"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import ClassifyResult, ProviderError
from app.ai.prompt_template import build_prompt, parse_response, preview_prompt
from app.ai.registry import get_provider
from app.classify.bill_item import ClassifyBillItem
from app.core.security import decrypt_secret
from app.models.ai import AiCredential, AiStrategy
from app.models.category import Category

logger = logging.getLogger(__name__)


@dataclass
class _Loaded:
    strategy: AiStrategy
    credential: AiCredential


async def _load(session: AsyncSession, user_id: int, strategy_id: int) -> _Loaded:
    strategy = await session.scalar(
        select(AiStrategy).where(AiStrategy.id == strategy_id, AiStrategy.user_id == user_id)
    )
    if not strategy:
        raise ProviderError(f"ai_strategy {strategy_id} not found for user {user_id}")
    if not strategy.credential_id:
        raise ProviderError(f"ai_strategy {strategy_id} has no credential bound")
    credential = await session.scalar(
        select(AiCredential).where(
            AiCredential.id == strategy.credential_id, AiCredential.user_id == user_id
        )
    )
    if not credential:
        raise ProviderError("ai_credential not found")
    if not credential.enabled:
        raise ProviderError("ai_credential disabled")
    return _Loaded(strategy=strategy, credential=credential)


def _split_rules(text: str) -> list[str]:
    """按行拆分用户填写的策略文本；空行与 # 注释忽略"""
    out: list[str] = []
    for line in (text or "").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        out.append(s)
    return out


async def classify_one(
    session: AsyncSession,
    *,
    user_id: int,
    strategy_id: int,
    bill: ClassifyBillItem,
    categories: list[Category],
) -> ClassifyResult:
    loaded = await _load(session, user_id, strategy_id)
    provider = get_provider(loaded.credential.provider)
    if not provider:
        raise ProviderError(f"provider {loaded.credential.provider!r} not registered")

    api_key = decrypt_secret(loaded.credential.api_key_encrypted)
    prompt = build_prompt(
        rules=_split_rules(loaded.strategy.strategy_text),
        category_names=[c.name for c in categories],
        bill=bill,
    )
    raw = await provider.chat(
        prompt=prompt,
        model=loaded.credential.model_name,
        api_key=api_key,
        base_url=loaded.credential.base_url,
    )
    cat = parse_response(raw, [c.name for c in categories])
    return ClassifyResult(category=cat, confidence=Decimal("0.80") if cat else None, raw=raw)


async def test_classify(
    session: AsyncSession,
    *,
    user_id: int,
    credential_id: int,
    strategy_id: int | None,
    sample: dict,
) -> ClassifyResult:
    """给前端 /ai/test 用：构造假 BillItem 跑一次"""
    from datetime import datetime

    if strategy_id is None:
        # 允许不绑定 strategy 跑一次纯 prompt（用空规则）
        credential = await session.scalar(
            select(AiCredential).where(
                AiCredential.id == credential_id, AiCredential.user_id == user_id
            )
        )
        if not credential:
            raise ProviderError("ai_credential not found")
        strategy_text = ""
    else:
        loaded = await _load(session, user_id, strategy_id)
        if loaded.credential.id != credential_id:
            raise ProviderError("credential_id mismatch with strategy")
        credential = loaded.credential
        strategy_text = loaded.strategy.strategy_text

    categories = list(await session.scalars(select(Category).where(Category.user_id == user_id)))
    fake = ClassifyBillItem(
        id=0,
        source=sample.get("source", "alipay"),
        payee=sample.get("payee"),
        item_name=sample.get("item_name"),
        amount=Decimal(str(sample.get("amount", "0.00"))),
        bill_type=sample.get("bill_type", "expense"),
        bill_time=datetime.now(),
    )
    provider = get_provider(credential.provider)
    if not provider:
        raise ProviderError(f"provider {credential.provider!r} not registered")
    api_key = decrypt_secret(credential.api_key_encrypted)
    prompt = build_prompt(
        rules=_split_rules(strategy_text),
        category_names=[c.name for c in categories],
        bill=fake,
    )
    raw = await provider.chat(
        prompt=prompt,
        model=credential.model_name,
        api_key=api_key,
        base_url=credential.base_url,
    )
    cat = parse_response(raw, [c.name for c in categories])
    return ClassifyResult(category=cat, confidence=Decimal("0.80") if cat else None, raw=raw)


def render_preview(strategy_text: str, category_names: list[str]) -> str:
    return preview_prompt(rules=_split_rules(strategy_text), category_names=category_names)
