"""AiClassifyStrategy 单测：通过 mock provider 跑通分类回写逻辑（不连真 LLM、不连真 DB）"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

import pytest

from app.classify.bill_item import ClassifyBillItem
from app.classify.context import ClassifyContext
from app.classify.strategy_types.ai_classify import AiClassifyStrategy


@dataclass
class FakeCategory:
    id: int
    name: str


@dataclass
class FakeStrategy:
    id: int
    user_id: int
    strategy_text: str = ""
    credential_id: int | None = 100


@dataclass
class FakeCredential:
    id: int = 100
    user_id: int = 1
    provider: str = "openai"
    model_name: str = "gpt-4o-mini"
    api_key_encrypted: str = "stub"
    base_url: str | None = None
    enabled: bool = True


@dataclass
class FakeSession:
    """只支持 .scalar(select(Model).where(...)) 的最小 stub"""

    strategy: FakeStrategy | None
    credential: FakeCredential | None
    calls: list[str] = field(default_factory=list)

    async def scalar(self, query):
        # 借用 SQLAlchemy compile + entity 名判断；简单识别：根据 select 的 entity
        try:
            entity = query.column_descriptions[0]["entity"]
        except Exception:
            entity = None
        name = getattr(entity, "__name__", "") if entity else ""
        if name == "AiStrategy":
            return self.strategy
        if name == "AiCredential":
            return self.credential
        return None


def _bill(bid: int, payee: str = "x", item: str = "y") -> ClassifyBillItem:
    return ClassifyBillItem(
        id=bid,
        source="alipay",
        payee=payee,
        item_name=item,
        amount=Decimal("1.00"),
        bill_type="expense",
        bill_time=datetime(2026, 1, 1, 12, 0),
    )


@pytest.fixture
def cats():
    return [FakeCategory(1, "餐饮"), FakeCategory(2, "交通"), FakeCategory(3, "购物")]


@pytest.fixture
def ctx_factory(cats):
    def _make(session):
        return ClassifyContext(user_id=1, session=session, step_id=42, categories=cats)
    return _make


@pytest.mark.asyncio
async def test_assigns_category_when_provider_returns_valid_name(monkeypatch, cats, ctx_factory):
    from app.ai.base import ClassifyResult
    from app.classify.strategy_types import ai_classify as mod

    async def fake_classify_one(session, *, user_id, strategy_id, bill, categories):
        if bill.payee == "星巴克":
            return ClassifyResult(category="餐饮", confidence=Decimal("0.9"), raw="餐饮")
        return ClassifyResult(category="交通", confidence=Decimal("0.7"), raw="交通")

    monkeypatch.setattr(mod, "classify_one", fake_classify_one)

    session = FakeSession(
        strategy=FakeStrategy(id=10, user_id=1, credential_id=100),
        credential=FakeCredential(),
    )
    items = [_bill(1, payee="星巴克"), _bill(2, payee="高德打车")]
    strat = AiClassifyStrategy()
    out = await strat.run(items, {"strategy_id": 10}, ctx_factory(session))

    assert out[0].category_id == 1
    assert out[0].classify_strategy_id == 42
    assert out[0].classify_strategy_type == "ai_classify"
    assert out[0].lifecycle == "classified"
    assert out[0].ai_provider == "openai"
    assert out[1].category_id == 2


@pytest.mark.asyncio
async def test_only_unclassified_filters_terminal_items(monkeypatch, cats, ctx_factory):
    from app.ai.base import ClassifyResult
    from app.classify.strategy_types import ai_classify as mod

    called: list[int] = []

    async def fake_classify_one(session, *, user_id, strategy_id, bill, categories):
        called.append(bill.id)
        return ClassifyResult(category="餐饮", confidence=Decimal("0.9"), raw="餐饮")

    monkeypatch.setattr(mod, "classify_one", fake_classify_one)

    session = FakeSession(
        strategy=FakeStrategy(id=10, user_id=1),
        credential=FakeCredential(),
    )
    pre = _bill(1)
    pre.category_id = 99
    pre.lifecycle = "classified"
    items = [pre, _bill(2), _bill(3)]
    items[2].lifecycle = "skipped"

    await AiClassifyStrategy().run(items, {"strategy_id": 10}, ctx_factory(session))
    assert called == [2]  # 仅未分类、未跳过的会被调


@pytest.mark.asyncio
async def test_unknown_category_name_is_ignored(monkeypatch, cats, ctx_factory):
    from app.ai.base import ClassifyResult
    from app.classify.strategy_types import ai_classify as mod

    async def fake_classify_one(*a, **kw):
        return ClassifyResult(category="不存在的类别", confidence=Decimal("0.5"), raw="...")

    monkeypatch.setattr(mod, "classify_one", fake_classify_one)
    session = FakeSession(strategy=FakeStrategy(10, 1), credential=FakeCredential())
    items = [_bill(1)]
    await AiClassifyStrategy().run(items, {"strategy_id": 10}, ctx_factory(session))
    assert items[0].category_id is None
    assert items[0].lifecycle == "unprocessed"


@pytest.mark.asyncio
async def test_provider_error_skips_item_without_failing_batch(monkeypatch, cats, ctx_factory):
    from app.ai.base import ClassifyResult, ProviderError
    from app.classify.strategy_types import ai_classify as mod

    async def fake_classify_one(session, *, user_id, strategy_id, bill, categories):
        if bill.id == 1:
            raise ProviderError("rate limited")
        return ClassifyResult(category="交通", confidence=Decimal("0.8"), raw="交通")

    monkeypatch.setattr(mod, "classify_one", fake_classify_one)
    session = FakeSession(strategy=FakeStrategy(10, 1), credential=FakeCredential())
    items = [_bill(1), _bill(2)]
    await AiClassifyStrategy().run(items, {"strategy_id": 10}, ctx_factory(session))
    assert items[0].category_id is None
    assert items[1].category_id == 2


def test_validate_params_rejects_bad_input():
    strat = AiClassifyStrategy()
    with pytest.raises(ValueError):
        strat.validate_params({})
    with pytest.raises(ValueError):
        strat.validate_params({"strategy_id": "10"})
    with pytest.raises(ValueError):
        strat.validate_params({"strategy_id": 10, "max_concurrency": 0})
    strat.validate_params({"strategy_id": 10})        # OK
    strat.validate_params({"strategy_id": 10, "max_concurrency": 8})  # OK
